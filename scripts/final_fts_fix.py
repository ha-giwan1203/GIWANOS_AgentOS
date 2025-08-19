# [EXPERIMENT] scripts/final_fts_fix.py
import sqlite3
import os

def final_fts_fix():
    db_path = 'C:/giwanos/data/velos.db'
    
    # DB 파일 백업
    backup_path = db_path + '.backup'
    if os.path.exists(db_path):
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✓ Database backed up to {backup_path}")
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    print("=== Final FTS Fix ===")
    
    # 모든 FTS 관련 객체 완전 삭제
    try:
        # 트리거 삭제
        cur.execute("DROP TRIGGER IF EXISTS trg_mem_ai")
        cur.execute("DROP TRIGGER IF EXISTS trg_mem_ad")
        cur.execute("DROP TRIGGER IF EXISTS trg_mem_au")
        
        # FTS 테이블 삭제
        cur.execute("DROP TABLE IF EXISTS memory_fts")
        
        # FTS 내부 테이블들 삭제
        cur.execute("DROP TABLE IF EXISTS memory_fts_data")
        cur.execute("DROP TABLE IF EXISTS memory_fts_idx")
        cur.execute("DROP TABLE IF EXISTS memory_fts_docsize")
        cur.execute("DROP TABLE IF EXISTS memory_fts_config")
        
        print("✓ All FTS objects dropped")
        
    except Exception as e:
        print(f"Error dropping: {e}")
    
    # 새로운 FTS 테이블 생성
    try:
        cur.execute("""
            CREATE VIRTUAL TABLE memory_fts USING fts5(
                text,
                content='memory',
                content_rowid='id'
            )
        """)
        print("✓ New FTS table created")
        
        # 트리거 생성
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
        
        # 기존 데이터 색인
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
        
        # 색인 최적화
        cur.execute("INSERT INTO memory_fts(memory_fts) VALUES('optimize')")
        print("✓ FTS index optimized")
        
        conn.commit()
        print("✓ All changes committed")
        
        # 테스트 검색
        cur.execute("SELECT rowid, text FROM memory_fts WHERE memory_fts MATCH 'test' LIMIT 3")
        test_results = cur.fetchall()
        print(f"✓ Test search found {len(test_results)} results")
        
    except Exception as e:
        print(f"Error creating: {e}")
        conn.rollback()
    
    conn.close()

if __name__ == "__main__":
    final_fts_fix()
