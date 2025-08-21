# [EXPERIMENT] VELOS 인덱스 검증 - 데이터베이스 무결성 검사
# [EXPERIMENT] scripts/check_all_indexes.py
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


def check_all_indexes():
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

    print("=== All Indexes Check ===")

    # 모든 인덱스 확인
    cur.execute("SELECT name, sql FROM sqlite_master WHERE type='index'")
    indexes = cur.fetchall()

    print("Indexes found:")
    for name, sql in indexes:
        print(f"\n=== Index: {name} ===")
        if sql:
            print(f"SQL: {sql}")

    conn.close()


if __name__ == "__main__":
    check_all_indexes()
