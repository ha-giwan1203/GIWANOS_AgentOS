# [EXPERIMENT] scripts/complete_fts_rebuild.py
import sqlite3
import os
import shutil

def complete_fts_rebuild():
    db_path = 'C:/giwanos/data/velos.db'
    
    print("=== Complete FTS Rebuild ===")
    
    # DB 백업
    backup_path = db_path + '.backup_fts'
    if os.path.exists(db_path):
        shutil.copy2(db_path, backup_path)
        print(f"✓ Database backed up to {backup_path}")
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    try:
        # 1. 모든 FTS 관련 객체 삭제
        print("\n1. Cleaning up FTS objects...")
        
        # 트리거 삭제
        triggers = ['trg_mem_ai', 'trg_mem_ad', 'trg_mem_au']
        for trigger in triggers:
            cur.execute(f"DROP TRIGGER IF EXISTS {trigger}")
        
        # FTS 테이블 삭제
        fts_tables = [
            'memory_fts', 'memory_fts_data', 'memory_fts_idx', 
            'memory_fts_docsize', 'memory_fts_config'
        ]
        for table in fts_tables:
            cur.execute(f"DROP TABLE IF EXISTS {table}")
        
        print("✓ All FTS objects dropped")
        
        # 2. 새로운 FTS 테이블 생성
        print("\n2. Creating new FTS table...")
        
        cur.execute("""
            CREATE VIRTUAL TABLE memory_fts USING fts5(
                text,
                content='memory',
                content_rowid='id'
            )
        """)
        print("✓ FTS table created")
        
        # 3. 트리거 생성
        print("\n3. Creating triggers...")
        
        cur.execute("""
            CREATE TRIGGER trg_mem_ai AFTER INSERT ON memory BEGIN
                INSERT INTO memory_fts(rowid, text) 
                VALUES (new.id, COALESCE(new.insight, new.raw, ''));
            END
        """)
        
        cur.execute("""
            CREATE TRIGGER trg_mem_ad AFTER DELETE ON memory BEGIN
                INSERT INTO memory_fts(memory_fts, rowid, text)
                VALUES('delete', old.id, COALESCE(old.insight, old.raw, ''));
            END
        """)
        
        cur.execute("""
            CREATE TRIGGER trg_mem_au AFTER UPDATE ON memory BEGIN
                INSERT INTO memory_fts(memory_fts, rowid, text)
                VALUES('delete', old.id, COALESCE(old.insight, old.raw, ''));
                INSERT INTO memory_fts(rowid, text) 
                VALUES (new.id, COALESCE(new.insight, new.raw, ''));
            END
        """)
        print("✓ Triggers created")
        
        # 4. 기존 데이터 색인
        print("\n4. Indexing existing data...")
        
        cur.execute("SELECT COUNT(*) FROM memory")
        total_records = cur.fetchone()[0]
        print(f"✓ Found {total_records} records in memory table")
        
        # 데이터 색인
        cur.execute("""
            INSERT INTO memory_fts(rowid, text) 
            SELECT id, COALESCE(insight, raw, '') FROM memory
        """)
        
        # 색인 확인
        cur.execute("SELECT COUNT(*) FROM memory_fts")
        fts_records = cur.fetchone()[0]
        print(f"✓ Indexed {fts_records} records in FTS table")
        
        # 5. 색인 최적화
        print("\n5. Optimizing FTS index...")
        cur.execute("INSERT INTO memory_fts(memory_fts) VALUES('optimize')")
        print("✓ FTS index optimized")
        
        conn.commit()
        print("\n✓ All changes committed successfully")
        
        # 6. 검증
        print("\n6. Verification...")
        
        # FTS 테이블 구조 확인
        cur.execute("PRAGMA table_info(memory_fts)")
        columns = cur.fetchall()
        print("FTS table columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # 테스트 검색
        test_terms = ['test', 'system', 'demo']
        for term in test_terms:
            cur.execute("SELECT COUNT(*) FROM memory_fts WHERE memory_fts MATCH ?", (term,))
            count = cur.fetchone()[0]
            print(f"✓ Search for '{term}': {count} results")
        
        # 샘플 검색 결과
        cur.execute("SELECT rowid, text FROM memory_fts WHERE memory_fts MATCH 'test' LIMIT 3")
        results = cur.fetchall()
        print(f"\nSample search results for 'test':")
        for i, (rowid, text) in enumerate(results, 1):
            print(f"  {i}. rowid={rowid}, text={text[:50]}...")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    complete_fts_rebuild()
