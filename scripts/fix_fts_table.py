# [EXPERIMENT] scripts/fix_fts_table.py
import sqlite3

def fix_fts_table():
    conn = sqlite3.connect('C:/giwanos/data/velos.db')
    cur = conn.cursor()
    
    print("=== FTS Table Complete Rebuild ===")
    
    # 기존 FTS 테이블과 트리거 완전 삭제
    try:
        cur.execute("DROP TABLE IF EXISTS memory_fts")
        cur.execute("DROP TABLE IF EXISTS memory_fts_data")
        cur.execute("DROP TABLE IF EXISTS memory_fts_idx")
        cur.execute("DROP TABLE IF EXISTS memory_fts_docsize")
        cur.execute("DROP TABLE IF EXISTS memory_fts_config")
        cur.execute("DROP TRIGGER IF EXISTS trg_mem_ai")
        cur.execute("DROP TRIGGER IF EXISTS trg_mem_ad")
        cur.execute("DROP TRIGGER IF EXISTS trg_mem_au")
        print("✓ All FTS tables and triggers dropped")
    except Exception as e:
        print(f"Error dropping: {e}")
    
    # 새로운 FTS 테이블 생성
    try:
        cur.execute("""
            CREATE VIRTUAL TABLE memory_fts USING fts5(
                text,
                content='memory',
                content_rowid='id',
                tokenize='unicode61'
            )
        """)
        print("✓ New FTS table created")
        
        # 트리거 생성
        cur.execute("""
            CREATE TRIGGER trg_mem_ai AFTER INSERT ON memory BEGIN
                INSERT INTO memory_fts(rowid, insight, raw) 
                VALUES (new.id, COALESCE(new.insight, new.raw, ''));
            END
        """)
        
        cur.execute("""
            CREATE TRIGGER trg_mem_ad AFTER DELETE ON memory BEGIN
                INSERT INTO memory_fts(memory_fts, rowid, insight, raw)
                VALUES('delete', old.id, COALESCE(old.insight, old.raw, ''));
            END
        """)
        
        cur.execute("""
            CREATE TRIGGER trg_mem_au AFTER UPDATE ON memory BEGIN
                INSERT INTO memory_fts(memory_fts, rowid, insight, raw)
                VALUES('delete', old.id, COALESCE(old.insight, old.raw, ''));
                INSERT INTO memory_fts(rowid, insight, raw) 
                VALUES (new.id, COALESCE(new.insight, new.raw, ''));
            END
        """)
        print("✓ Triggers created")
        
        # 기존 데이터로 FTS 테이블 채우기
        cur.execute("SELECT COUNT(*) FROM memory")
        total_records = cur.fetchone()[0]
        print(f"✓ Found {total_records} records in memory table")
        
        cur.execute("""
            INSERT INTO memory_fts(rowid, insight, raw) 
            SELECT id, COALESCE(insight, raw, '') FROM memory
        """)
        
        # FTS 테이블 확인
        cur.execute("SELECT COUNT(*) FROM memory_fts")
        fts_records = cur.fetchone()[0]
        print(f"✓ Indexed {fts_records} records in FTS table")
        
        conn.commit()
        print("✓ All changes committed")
        
    except Exception as e:
        print(f"Error creating: {e}")
        conn.rollback()
    
    conn.close()

if __name__ == "__main__":
    fix_fts_table()


