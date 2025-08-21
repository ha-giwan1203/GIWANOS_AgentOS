# [EXPERIMENT] scripts/fts_structure_fix.py
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
        return "/home/user/webapp"

    def get_data_path(*parts):
        return os.path.join("/home/user/webapp", "data", *parts)

    def get_config_path(*parts):
        return os.path.join("/home/user/webapp", "configs", *parts)

    def get_db_path():
        return "/home/user/webapp/data/memory/velos.db"


def fts_structure_fix():
    db_path = (
        get_db_path()
        if "get_db_path" in locals()
        else (
            get_data_path("memory/velos.db")
            if "get_data_path" in locals()
            else "/home/user/webapp/data/memory/velos.db"
        )
    )

    print("=== FTS Structure Fix ===")

    # DB 백업
    backup_path = db_path + ".backup_structure"
    if os.path.exists(db_path):
        shutil.copy2(db_path, backup_path)
        print(f"✓ Database backed up to {backup_path}")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        # 1. 현재 FTS 테이블 구조 확인
        print("\n1. Checking current FTS table structure...")

        cur.execute("PRAGMA table_info(memory_fts)")
        columns = cur.fetchall()
        print("Current FTS table columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")

        # 2. 모든 FTS 관련 객체 완전 삭제
        print("\n2. Complete cleanup of FTS objects...")

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

        print("✓ All FTS objects dropped")

        # 3. 새로운 FTS 테이블 생성 (외부 컨텐츠 없이)
        print("\n3. Creating new FTS table without external content...")

        cur.execute(
            """
            CREATE VIRTUAL TABLE memory_fts USING fts5(
                text
            )
        """
        )
        print("✓ FTS table created")

        # 4. 트리거 생성
        print("\n4. Creating triggers...")

        cur.execute(
            """
            CREATE TRIGGER trg_mem_ai AFTER INSERT ON memory BEGIN
                INSERT INTO memory_fts(text) 
                VALUES (COALESCE(new.insight, new.raw, ''));
            END
        """
        )

        cur.execute(
            """
            CREATE TRIGGER trg_mem_ad AFTER DELETE ON memory BEGIN
                INSERT INTO memory_fts(memory_fts, text)
                VALUES('delete', COALESCE(old.insight, old.raw, ''));
            END
        """
        )

        cur.execute(
            """
            CREATE TRIGGER trg_mem_au AFTER UPDATE ON memory BEGIN
                INSERT INTO memory_fts(memory_fts, text)
                VALUES('delete', COALESCE(old.insight, old.raw, ''));
                INSERT INTO memory_fts(text) 
                VALUES (COALESCE(new.insight, new.raw, ''));
            END
        """
        )
        print("✓ Triggers created")

        # 5. 기존 데이터 색인
        print("\n5. Indexing existing data...")

        cur.execute("SELECT COUNT(*) FROM memory")
        total_records = cur.fetchone()[0]
        print(f"✓ Found {total_records} records in memory table")

        # 데이터 색인 (빈 문자열 제외)
        cur.execute(
            """
            INSERT INTO memory_fts(text) 
            SELECT COALESCE(insight, raw, '') 
            FROM memory 
            WHERE COALESCE(insight, raw, '') <> ''
        """
        )

        # 색인 확인
        cur.execute("SELECT COUNT(*) FROM memory_fts")
        fts_records = cur.fetchone()[0]
        print(f"✓ Indexed {fts_records} records in FTS table")

        # 6. 색인 최적화
        print("\n6. Optimizing FTS index...")
        cur.execute("INSERT INTO memory_fts(memory_fts) VALUES('optimize')")
        print("✓ FTS index optimized")

        conn.commit()
        print("\n✓ All changes committed successfully")

        # 7. 검증
        print("\n7. Verification...")

        # FTS 테이블 구조 확인
        cur.execute("PRAGMA table_info(memory_fts)")
        columns = cur.fetchall()
        print("New FTS table columns:")
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

        # 8. 뷰 재생성
        print("\n8. Recreating views...")

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
    fts_structure_fix()
