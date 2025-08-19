# [EXPERIMENT] scripts/check_triggers.py
import sqlite3

def check_triggers():
    conn = sqlite3.connect('C:/giwanos/data/velos.db')
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
