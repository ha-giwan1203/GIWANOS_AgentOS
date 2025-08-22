# [EXPERIMENT] scripts/simple_fts_test.py
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


def simple_fts_test():
    conn = sqlite3.connect(
        get_db_path()
        if "get_db_path" in locals()
        else (
            get_data_path("memory/velos.db")
            if "get_data_path" in locals()
            else "/home/user/webapp/data/memory/velos.db"
        )
    )
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
