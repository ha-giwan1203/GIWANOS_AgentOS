# [ACTIVE] VELOS 운영 철학 선언문
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.
"""

import sqlite3
import os
import time


def fts_healthcheck():
    """FTS5 검색 기능의 정상 동작을 검증합니다."""
    db = os.getenv("VELOS_DB_PATH", r"C:\giwanos\data\velos.db")
    
    if not os.path.exists(db):
        print(f"ERROR: Database not found: {db}")
        return False
    
    try:
        con = sqlite3.connect(db, isolation_level=None)
        c = con.cursor()
        
        def hit(q, rid=None):
            """검색어가 특정 rowid에서 매치되는지 확인"""
            if rid is None:
                return c.execute(
                    "SELECT 1 FROM memory_fts WHERE memory_fts MATCH ? LIMIT 1", 
                    (q,)
                ).fetchone() is not None
            return c.execute(
                "SELECT 1 FROM memory_fts WHERE rowid=? AND memory_fts MATCH ? LIMIT 1", 
                (rid, q)
            ).fetchone() is not None
        
        # term/prefix/join 테스트
        c.execute(
            "INSERT INTO memory(ts,role,insight,raw) VALUES (strftime('%s','now'),'probe','omega prefix case','r')"
        )
        rid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        # 기본 검색과 접두사 검색 테스트
        assert hit("omega") and hit("ome*")
        
        # JOIN 테스트
        assert c.execute(
            """SELECT 1 FROM memory_fts f JOIN memory m ON m.id=f.rowid
               WHERE memory_fts MATCH ? LIMIT 1""", 
            ("omega",)
        ).fetchone()
        
        # tombstone 흐름 테스트
        a0 = hit("omega", rid)
        c.execute("UPDATE memory SET insight='sigma prefix case' WHERE id=?", (rid,))
        time.sleep(0.05)
        a1 = hit("omega", rid)
        b1 = hit("sigma", rid)
        c.execute("DELETE FROM memory WHERE id=?", (rid,))
        time.sleep(0.05)
        b2 = hit("sigma", rid)
        
        # 검증: 업데이트 후 이전 검색어는 안 나와야 하고, 삭제 후는 아무것도 안 나와야 함
        assert a0 and (not a1) and b1 and (not b2)
        
        print("fts_healthcheck: OK")
        return True
        
    except Exception as e:
        print(f"ERROR: FTS healthcheck failed: {e}")
        return False
    finally:
        if 'con' in locals():
            con.close()


if __name__ == "__main__":
    success = fts_healthcheck()
    exit(0 if success else 1)
