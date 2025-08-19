# [ACTIVE] VELOS 운영 철학 선언문
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.
"""

import sqlite3
import os


def check_schema_guard():
    """스키마 버전과 필수 트리거 존재 여부를 검증합니다."""
    db = os.getenv("VELOS_DB_PATH", r"C:\giwanos\data\velos.db")
    
    if not os.path.exists(db):
        print(f"ERROR: Database not found: {db}")
        return False
    
    try:
        con = sqlite3.connect(db)
        cur = con.cursor()
        
        # 스키마 버전 검증
        v = cur.execute("PRAGMA user_version").fetchone()[0]
        need = 2
        if v < need:
            print(f"ERROR: Schema too old: {v} < {need}")
            return False
        
        # 필수 트리거 존재 여부 검증
        req = {"trg_mem_ai", "trg_mem_bu", "trg_mem_au", "trg_mem_bd"}
        have = {r[0] for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='memory'"
        )}
        missing = req - have
        
        if missing:
            print(f"ERROR: Missing triggers: {sorted(missing)}")
            return False
        
        print("schema_guard: OK")
        return True


    except Exception as e:
        print(f"ERROR: Schema guard check failed: {e}")
        return False
    finally:
        if 'con' in locals():
            con.close()

if __name__ == "__main__":
    success = check_schema_guard()
    exit(0 if success else 1)
