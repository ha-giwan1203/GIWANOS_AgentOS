# [EXPERIMENT] scripts/test_fts_triggers.py
import sqlite3
import time
import os

def test_fts_triggers():
    db = os.environ.get("VELOS_DB_PATH", r"C:\giwanos\data\velos.db")
    print(f"Testing FTS triggers with DB: {db}")
    
    try:
        con = sqlite3.connect(db)
        c = con.cursor()
        
        # 1) insert
        ts = int(time.time())
        c.execute(
            "INSERT INTO memory(ts, role, insight, raw) VALUES(?,?,?,?)",
            (ts, "test", "fts trigger self-check", None)
        )
        mid = c.lastrowid
        con.commit()
        print(f"Inserted record with id: {mid}")
        
        # 2) fts should see it
        n = c.execute("SELECT COUNT(*) FROM memory_fts WHERE rowid=?", (mid,)).fetchone()[0]
        print(f"After insert, FTS rows for new id: {n}")
        
        # 3) update
        c.execute("UPDATE memory SET insight=? WHERE id=?", ("fts trigger updated", mid))
        con.commit()
        print(f"Updated record {mid}")
        
        n2 = c.execute("SELECT COUNT(*) FROM memory_fts WHERE insight LIKE '%updated%'", (mid,)).fetchone()[0]
        print(f"After update, FTS updated seen: {n2}")
        
        # 4) delete
        c.execute("DELETE FROM memory WHERE id=?", (mid,))
        con.commit()
        print(f"Deleted record {mid}")
        
        n3 = c.execute("SELECT COUNT(*) FROM memory_fts WHERE rowid=?", (mid,)).fetchone()[0]
        print(f"After delete, FTS rows for id: {n3}")
        
        con.close()
        print("Test completed successfully")
        
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    test_fts_triggers()


