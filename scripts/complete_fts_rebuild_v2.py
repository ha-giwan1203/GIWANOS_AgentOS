# [EXPERIMENT] scripts/complete_fts_rebuild_v2.py
import os
import shutil
import sqlite3

# Path manager imports (Phase 2 standardization)
try:
    from modules.core.path_manager import (
        get_config_path,
        get_data_path,
        get_db_path,
        get_velos_root,
    )
except ImportError:
    # Fallback functions for backward compatibility
    def get_velos_root():
        return "C:\giwanos"

    def get_data_path(*parts):
        return os.path.join("C:\giwanos", "data", *parts)

    def get_config_path(*parts):
        return os.path.join("C:\giwanos", "configs", *parts)

    def get_db_path():
        return "C:\giwanos/data/memory/velos.db"


def complete_fts_rebuild_v2():
    db_path = (
        get_db_path()
        if "get_db_path" in locals()
        else (
            get_data_path("memory/velos.db")
            if "get_data_path" in locals()
            else "C:\giwanos/data/memory/velos.db"
        )
    )

    print("=== Complete FTS Rebuild v2 ===")

    # DB 백업
    backup_path = db_path + ".backup_v2"
    if os.path.exists(db_path):
        shutil.copy2(db_path, backup_path)
        print(f"✓ Database backed up to {backup_path}")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        # 1. 모든 FTS 관련 객체 완전 삭제
        print("\n1. Complete cleanup of FTS objects...")

        # 트리거 삭제
        triggers = ["trg_mem_ai", "trg_mem_ad", "trg_mem_au"]
        for trigger in triggers:
            cur.execute(f"DROP TRIGGER IF EXISTS {trigger}")

        # FTS 테이블 및 관련 테이블 삭제
        fts_tables = [
            "memory_fts",
            "memory_fts_data",
            "memory_fts_idx",
            "memory_fts_docsize",
            "memory_fts_config",
        ]
        for table in fts_tables:
            cur.execute(f"DROP TABLE IF EXISTS {table}")

        # 뷰 삭제 (FTS 관련)
        cur.execute("SELECT name FROM sqlite_master WHERE type='view' AND sql LIKE '%memory_fts%'")
        fts_views = cur.fetchall()
        for view in fts_views:
            cur.execute(f"DROP VIEW IF EXISTS {view[0]}")

        print("✓ All FTS objects dropped")

        # 2. 새로운 FTS 테이블 생성 (단순화된 버전)
        print("\n2. Creating new FTS table...")

        cur.execute(
            """
            CREATE VIRTUAL TABLE memory_fts USING fts5(
                text,
                content='memory',
                content_rowid='id'
            )
        """
        )
        print("✓ FTS table created")

        # 3. 트리거 생성
        print("\n3. Creating triggers...")

        cur.execute(
            """
            CREATE TRIGGER trg_mem_ai AFTER INSERT ON memory BEGIN
                INSERT INTO memory_fts(rowid, text) 
                VALUES (new.id, COALESCE(new.insight, new.raw, ''));
            END
        """
        )

        cur.execute(
            """
            CREATE TRIGGER trg_mem_ad AFTER DELETE ON memory BEGIN
                INSERT INTO memory_fts(memory_fts, rowid, text)
                VALUES('delete', old.id, COALESCE(old.insight, old.raw, ''));
            END
        """
        )

        cur.execute(
            """
            CREATE TRIGGER trg_mem_au AFTER UPDATE ON memory BEGIN
                INSERT INTO memory_fts(memory_fts, rowid, text)
                VALUES('delete', old.id, COALESCE(old.insight, old.raw, ''));
                INSERT INTO memory_fts(rowid, text) 
                VALUES (new.id, COALESCE(new.insight, new.raw, ''));
            END
        """
        )
        print("✓ Triggers created")

        # 4. 기존 데이터 색인
        print("\n4. Indexing existing data...")

        cur.execute("SELECT COUNT(*) FROM memory")
        total_records = cur.fetchone()[0]
        print(f"✓ Found {total_records} records in memory table")

        # 데이터 색인 (빈 문자열 제외)
        cur.execute(
            """
            INSERT INTO memory_fts(rowid, text) 
            SELECT id, COALESCE(insight, raw, '') 
            FROM memory 
            WHERE COALESCE(insight, raw, '') <> ''
        """
        )

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
        test_terms = ["test", "system", "demo", "검색어"]
        for term in test_terms:
            try:
                cur.execute("SELECT COUNT(*) FROM memory_fts WHERE memory_fts MATCH ?", (term,))
                count = cur.fetchone()[0]
                print(f"✓ Search for '{term}': {count} results")
            except Exception as e:
                print(f"✗ Search for '{term}': Error - {e}")

        # 샘플 검색 결과
        try:
            cur.execute("SELECT rowid, text FROM memory_fts WHERE memory_fts MATCH 'test' LIMIT 3")
            results = cur.fetchall()
            print(f"\nSample search results for 'test':")
            for i, (rowid, text) in enumerate(results, 1):
                print(f"  {i}. rowid={rowid}, text={text[:50]}...")
        except Exception as e:
            print(f"✗ Sample search error: {e}")

        # 7. 뷰 재생성
        print("\n7. Recreating views...")

        cur.executescript(
            """
            CREATE VIEW memory_compat AS
            SELECT id, ts, role, insight AS text FROM memory;

            CREATE VIEW memory_roles AS
            SELECT id, ts, role, '' AS source, insight AS text FROM memory;

            CREATE VIEW memory_text AS
            SELECT id, ts, role, '[]' AS tags, insight AS text_norm FROM memory;
        """
        )

        print("✓ Views recreated")

        conn.commit()
        print("✓ Final commit completed")

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    complete_fts_rebuild_v2()
