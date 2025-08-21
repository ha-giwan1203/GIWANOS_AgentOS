# [EXPERIMENT] scripts/rebuild_all_views.py
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


def rebuild_all_views():
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

    print("=== Rebuild All Views ===")

    # 기존 뷰 삭제
    cur.execute("SELECT name FROM sqlite_master WHERE type='view'")
    views = cur.fetchall()

    for view in views:
        view_name = view[0]
        cur.execute(f"DROP VIEW IF EXISTS {view_name}")
        print(f"✓ Dropped view: {view_name}")

    # 새로운 뷰 생성
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

    print("✓ All views recreated")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    rebuild_all_views()
