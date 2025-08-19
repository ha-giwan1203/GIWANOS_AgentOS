# [EXPERIMENT] scripts/check_fts_data.py
import sqlite3

def check_fts_data():
    conn = sqlite3.connect('C:/giwanos/data/velos.db')
    cur = conn.cursor()
    
    print("=== FTS Data Check ===")
    
    # FTS 테이블 구조 확인
    cur.execute("PRAGMA table_info(memory_fts)")
    columns = cur.fetchall()
    print("FTS table columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # FTS 테이블 데이터 확인
    cur.execute("SELECT COUNT(*) FROM memory_fts")
    fts_count = cur.fetchone()[0]
    print(f"\nFTS table record count: {fts_count}")
    
    # FTS 테이블 샘플 데이터
    cur.execute("SELECT rowid, text FROM memory_fts LIMIT 5")
    rows = cur.fetchall()
    print(f"\nFTS sample data ({len(rows)} rows):")
    for i, (rowid, text) in enumerate(rows, 1):
        print(f"  {i}. rowid={rowid}, text={text[:50]}...")
    
    # memory 테이블과 비교
    cur.execute("SELECT COUNT(*) FROM memory")
    memory_count = cur.fetchone()[0]
    print(f"\nMemory table record count: {memory_count}")
    
    # memory 테이블 샘플 데이터
    cur.execute("SELECT id, insight FROM memory LIMIT 5")
    rows = cur.fetchall()
    print(f"\nMemory sample data ({len(rows)} rows):")
    for i, (id_val, insight) in enumerate(rows, 1):
        print(f"  {i}. id={id_val}, insight={insight[:50]}...")
    
    conn.close()

if __name__ == "__main__":
    check_fts_data()
