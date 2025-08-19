# [EXPERIMENT] VELOS 스키마 검증 - 데이터베이스 구조 검사
# [EXPERIMENT] scripts/check_db_schema.py
import sqlite3

def check_db_schema():
    conn = sqlite3.connect('C:/giwanos/data/velos.db')
    cur = conn.cursor()
    
    # 테이블 목록 확인
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cur.fetchall()
    print("Tables:", [t[0] for t in tables])
    
    # memory 테이블 스키마 확인
    if ('memory',) in tables:
        cur.execute("PRAGMA table_info(memory)")
        columns = cur.fetchall()
        print("\nMemory table columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
    
    # memory_fts 테이블 확인
    if ('memory_fts',) in tables:
        cur.execute("PRAGMA table_info(memory_fts)")
        columns = cur.fetchall()
        print("\nMemory_fts table columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
    
    conn.close()

if __name__ == "__main__":
    check_db_schema()
