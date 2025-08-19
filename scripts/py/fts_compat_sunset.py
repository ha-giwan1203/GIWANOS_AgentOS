# [ACTIVE] VELOS FTS 호환 뷰 일몰 스케줄러
# T+60일에 memory_fts_text/memory_fts_compat 제거 예정

import sqlite3
import datetime
from pathlib import Path

def create_sunset_reminder():
    """호환 뷰 일몰 리마인더 생성"""
    sunset_date = datetime.date.today() + datetime.timedelta(days=60)
    
    db = Path(r"C:\giwanos\data\velos.db")
    con = sqlite3.connect(db, isolation_level=None)
    c = con.cursor()
    
    c.executescript(f"""
    BEGIN IMMEDIATE;
    CREATE TABLE IF NOT EXISTS fts_compat_sunset (
        sunset_date TEXT,
        notice TEXT,
        created_at INTEGER DEFAULT (strftime('%s','now'))
    );
    INSERT OR REPLACE INTO fts_compat_sunset (sunset_date, notice) 
    VALUES ('{sunset_date}', 'T+60days deprecation: remove memory_fts_text/memory_fts_compat');
    COMMIT;
    """)
    
    print(f"Sunset reminder created: {sunset_date}")
    con.close()

def check_sunset_status():
    """일몰 상태 확인"""
    db = Path(r"C:\giwanos\data\velos.db")
    con = sqlite3.connect(db)
    c = con.cursor()
    
    try:
        c.execute("SELECT sunset_date, notice FROM fts_compat_sunset LIMIT 1")
        result = c.fetchone()
        if result:
            sunset_date, notice = result
            today = datetime.date.today().isoformat()
            if today >= sunset_date:
                print(f"⚠️ SUNSET ALERT: {notice}")
                print(f"Action required: Remove compatibility views")
                return True
            else:
                days_left = (datetime.date.fromisoformat(sunset_date) - datetime.date.today()).days
                print(f"Sunset countdown: {days_left} days until {sunset_date}")
                return False
    except Exception as e:
        print(f"Sunset check failed: {e}")
        return False
    finally:
        con.close()

if __name__ == "__main__":
    create_sunset_reminder()
    check_sunset_status()
