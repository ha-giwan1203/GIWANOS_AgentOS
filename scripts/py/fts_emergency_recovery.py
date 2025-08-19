# [ACTIVE] VELOS 운영 철학 선언문
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

FTS 긴급 복구 스크립트
문제 발생 시 즉시 실행하여 재색인+최적화+체크포인트를 수행합니다.
"""

import os
import sqlite3
import sys
import time


def fts_emergency_recovery():
    """FTS 긴급 복구 - 재색인+최적화+체크포인트"""
    db = os.environ.get("VELOS_DB_PATH", r"C:\giwanos\data\velos.db")
    
    if not os.path.exists(db):
        print(f"ERROR: 데이터베이스 파일이 존재하지 않습니다: {db}")
        return False
    
    print(f"FTS 긴급 복구 시작: {db}")
    print(f"시작 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        con = sqlite3.connect(db, isolation_level=None)
        c = con.cursor()
        
        # 1단계: 재색인 시도
        print("1단계: FTS 재색인 시도...")
        try:
            c.executescript("""
                BEGIN IMMEDIATE;
                INSERT INTO memory_fts(memory_fts) VALUES('rebuild');
                COMMIT;
            """)
            print("FTS 재색인 성공")
        except Exception as e:
            print(f"FTS 재색인 실패, 수동 재구성 시도: {e}")
            
            # 2단계: 수동 재구성
            print("2단계: 수동 FTS 재구성...")
            c.executescript("""
                BEGIN IMMEDIATE;
                DELETE FROM memory_fts;
                INSERT INTO memory_fts(rowid, insight, raw) 
                SELECT id, insight, raw FROM memory;
                COMMIT;
            """)
            print("수동 FTS 재구성 완료")
        
        # 3단계: 최적화
        print("3단계: FTS 최적화...")
        c.executescript("INSERT INTO memory_fts(memory_fts) VALUES('optimize');")
        print("FTS 최적화 완료")
        
        # 4단계: WAL 체크포인트
        print("4단계: WAL 체크포인트...")
        checkpoint_result = c.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchall()
        print(f"WAL 체크포인트 결과: {checkpoint_result}")
        
        # 5단계: 무결성 검사
        print("5단계: 데이터베이스 무결성 검사...")
        integrity_result = c.execute("PRAGMA integrity_check").fetchall()
        if integrity_result[0][0] == "ok":
            print("무결성 검사 통과")
        else:
            print(f"무결성 검사 실패: {integrity_result}")
            return False
        
        con.close()
        
        print(f"FTS 긴급 복구 완료: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        return True
        
    except Exception as e:
        print(f"ERROR: FTS 긴급 복구 실패: {e}")
        return False


if __name__ == "__main__":
    success = fts_emergency_recovery()
    exit(0 if success else 1)
