# [EXPERIMENT] scripts/check_fts_health.py
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
        return "/home/user/webapp"

    def get_data_path(*parts):
        return os.path.join("/home/user/webapp", "data", *parts)

    def get_config_path(*parts):
        return os.path.join("/home/user/webapp", "configs", *parts)

    def get_db_path():
        return "/home/user/webapp/data/memory/velos.db"


def check_fts_health():
    db_path = (
        get_db_path()
        if "get_db_path" in locals()
        else (
            get_data_path("memory/velos.db")
            if "get_data_path" in locals()
            else "/home/user/webapp/data/memory/velos.db"
        )
    )

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # FTS 테이블 존재 확인
        cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='memory_fts'")
        fts_exists = cur.fetchone() is not None

        if not fts_exists:
            print("FTS status=ERROR, message=memory_fts table not found")
            return

        # FTS 테이블 레코드 수 확인
        cur.execute("SELECT COUNT(*) FROM memory_fts")
        fts_rows = cur.fetchone()[0]

        # FTS 테이블 구조 확인
        cur.execute("PRAGMA table_info(memory_fts)")
        columns = cur.fetchall()
        has_text_column = any(col[1] == "text" for col in columns)

        # 테스트 검색 실행
        test_success = False
        try:
            cur.execute("SELECT COUNT(*) FROM memory_fts WHERE memory_fts MATCH 'test'")
            test_count = cur.fetchone()[0]
            test_success = True
        except sqlite3.Error:
            test_success = False

        conn.close()

        # 상태 판정
        if fts_exists and has_text_column and test_success:
            print(f"FTS status=OK, rows={fts_rows}")
        else:
            issues = []
            if not fts_exists:
                issues.append("table_missing")
            if not has_text_column:
                issues.append("no_text_column")
            if not test_success:
                issues.append("search_failed")
            print(f"FTS status=ERROR, issues={','.join(issues)}, rows={fts_rows}")

    except Exception as e:
        print(f"FTS status=ERROR, message={str(e)}")


if __name__ == "__main__":
    check_fts_health()
