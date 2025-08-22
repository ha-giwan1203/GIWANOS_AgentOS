# [EXPERIMENT] scripts/run_fts_lockin.py
import os
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


def run_fts_lockin():
    db_path = (
        get_db_path()
        if "get_db_path" in locals()
        else (
            get_data_path("memory/velos.db")
            if "get_data_path" in locals()
            else "C:\giwanos/data/memory/velos.db"
        )
    )
    sql_path = "scripts/sql/fts_lockin_v1.sql"

    print(f"[run_fts_lockin] DB={db_path}")
    print(f"[run_fts_lockin] SQL={sql_path}")

    # SQL 파일 읽기
    with open(sql_path, "r", encoding="utf-8") as f:
        sql_script = f.read()

    # DB 연결 및 실행
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        print("[run_fts_lockin] Executing SQL script...")
        cur.executescript(sql_script)
        print("[run_fts_lockin] SQL script executed successfully")

        # 검증
        cur.execute("SELECT COUNT(*) FROM memory_fts")
        count = cur.fetchone()[0]
        print(f"[run_fts_lockin] FTS table has {count} records")

        # 테스트 검색
        test_terms = ["test", "system", "demo", "검색어"]
        for term in test_terms:
            cur.execute("SELECT COUNT(*) FROM memory_fts WHERE memory_fts MATCH ?", (term,))
            result_count = cur.fetchone()[0]
            print(f"[run_fts_lockin] Search '{term}': {result_count} results")

        conn.commit()
        print("[run_fts_lockin] OK")

    except Exception as e:
        print(f"[run_fts_lockin] FAILED: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run_fts_lockin()
