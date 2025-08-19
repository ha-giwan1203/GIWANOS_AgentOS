# [EXPERIMENT] VELOS 테이블 검증 - 데이터베이스 테이블 검사
# -*- coding: utf-8 -*-
"""
VELOS 운영 철학 선언문
"판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다."

데이터베이스 테이블 확인 스크립트
"""

import sqlite3
from pathlib import Path

def check_database_tables():
    """데이터베이스 테이블 확인"""
    db_path = Path("data/velos.db")
    
    if not db_path.exists():
        print("❌ 데이터베이스 파일이 없습니다")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 테이블 목록 조회
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print("📊 현재 테이블 목록:")
        for table in tables:
            print(f"  - {table}")
        
        # memory_roles 테이블 확인
        if 'memory_roles' in tables:
            print("✅ memory_roles 테이블 존재")
            
            # 테이블 구조 확인
            cursor.execute("PRAGMA table_info(memory_roles)")
            columns = cursor.fetchall()
            print("📋 memory_roles 테이블 구조:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        else:
            print("❌ memory_roles 테이블 없음")
            
            # 테이블 생성
            print("🔧 memory_roles 테이블 생성 중...")
            cursor.execute("""
                CREATE TABLE memory_roles (
                    id INTEGER PRIMARY KEY,
                    role TEXT NOT NULL,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("✅ memory_roles 테이블 생성 완료")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 오류: {e}")
        return False

if __name__ == "__main__":
    check_database_tables()

