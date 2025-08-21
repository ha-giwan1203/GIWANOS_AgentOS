# [EXPERIMENT] scripts/check_triggers.py
import sqlite3

# Path manager imports (Phase 2 standardization)
try:
    from modules.core.path_manager import get_velos_root, get_data_path, get_config_path, get_db_path
except ImportError:
    # Fallback functions for backward compatibility
    def get_velos_root(): return "C:/giwanos"
    def get_data_path(*parts): return os.path.join("C:/giwanos", "data", *parts)
    def get_config_path(*parts): return os.path.join("C:/giwanos", "configs", *parts)
    def get_db_path(): return "C:/giwanos/data/memory/velos.db"

def check_triggers():
    conn = sqlite3.connect(get_db_path() if "get_db_path" in locals() else get_data_path("memory/velos.db") if "get_data_path" in locals() else "C:/giwanos/data/memory/velos.db")
    cur = conn.cursor()
    
    # 트리거 목록 확인
    cur.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
    triggers = cur.fetchall()
    print("Triggers:", [t[0] for t in triggers])
    
    # 각 트리거의 내용 확인
    for trigger in triggers:
        trigger_name = trigger[0]
        print(f"\n=== Trigger: {trigger_name} ===")
        cur.execute("SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?", (trigger_name,))
        sql = cur.fetchone()
        if sql:
            print(sql[0])
    
    conn.close()

if __name__ == "__main__":
    check_triggers()
