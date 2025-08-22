# [EXPERIMENT] VELOS 객체 검증 - 데이터베이스 스키마 검사
# [EXPERIMENT] scripts/check_all_objects.py
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


def check_all_objects():
    conn = sqlite3.connect(
        get_db_path()
        if "get_db_path" in locals()
        else (
            get_data_path("memory/velos.db")
            if "get_data_path" in locals()
            else "C:\giwanos/data/memory/velos.db"
        )
    )
    cur = conn.cursor()

    print("=== All Database Objects ===")

    # 모든 객체 확인
    cur.execute(
        "SELECT name, type, sql FROM sqlite_master WHERE name IS NOT NULL ORDER BY type, name"
    )
    objects = cur.fetchall()

    for name, obj_type, sql in objects:
        print(f"\n=== {obj_type.upper()}: {name} ===")
        if sql:
            print(f"SQL: {sql[:200]}...")

    conn.close()


if __name__ == "__main__":
    check_all_objects()
