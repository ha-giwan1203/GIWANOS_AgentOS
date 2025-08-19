# [EXPERIMENT] scripts/simple_fts_test.py
import sqlite3

def simple_fts_test():
    conn = sqlite3.connect('C:/giwanos/data/velos.db')
    cur = conn.cursor()
    
    print("=== Simple FTS Test ===")
    
    # SQLite 버전 확인
    cur.execute("SELECT sqlite_version()")
    version = cur.fetchone()[0]
    print(f"SQLite version: {version}")
    
    # FTS5 지원 확인
    try:
        cur.execute("SELECT fts5(?)", ("test",))
        print("✓ FTS5 is available")
    except Exception as e:
        print(f"✗ FTS5 not available: {e}")
        return
    
    # 간단한 FTS 테이블 생성 테스트
    try:
        cur.execute("DROP TABLE IF EXISTS test_fts")
        cur.execute("CREATE VIRTUAL TABLE test_fts USING fts5(text)")
        cur.execute("INSERT INTO test_fts(text) VALUES('hello world')")
        cur.execute("SELECT * FROM test_fts WHERE test_fts MATCH 'hello'")
        results = cur.fetchall()
        print(f"✓ Simple FTS test successful: {len(results)} results")
        cur.execute("DROP TABLE test_fts")
    except Exception as e:
        print(f"✗ Simple FTS test failed: {e}")
    
    conn.close()

if __name__ == "__main__":
    simple_fts_test()
