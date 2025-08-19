# [EXPERIMENT] scripts/cleanup_all_fts.py
import sqlite3

def cleanup_all_fts():
    conn = sqlite3.connect('C:/giwanos/data/velos.db')
    cur = conn.cursor()
    
    print("=== Complete FTS Cleanup ===")
    
    # 모든 FTS 관련 객체 찾기
    cur.execute("SELECT name, type FROM sqlite_master WHERE name LIKE '%fts%' OR name LIKE '%trg_mem%'")
    fts_objects = cur.fetchall()
    
    print("Found FTS-related objects:")
    for name, obj_type in fts_objects:
        print(f"  {obj_type}: {name}")
    
    # 모든 FTS 관련 객체 삭제
    for name, obj_type in fts_objects:
        try:
            if obj_type == 'table':
                cur.execute(f"DROP TABLE IF EXISTS {name}")
            elif obj_type == 'trigger':
                cur.execute(f"DROP TRIGGER IF EXISTS {name}")
            elif obj_type == 'view':
                cur.execute(f"DROP VIEW IF EXISTS {name}")
            print(f"✓ Dropped {obj_type}: {name}")
        except Exception as e:
            print(f"Error dropping {name}: {e}")
    
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
        
        cur.execute("""
            INSERT INTO memory_fts(rowid, text) 
            SELECT id, COALESCE(insight, raw, '') FROM memory
        """)
        
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
    cleanup_all_fts()
