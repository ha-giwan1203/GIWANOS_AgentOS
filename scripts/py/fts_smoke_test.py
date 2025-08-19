# [ACTIVE] FTS 스모크 테스트
import os, sqlite3, time
ROOT = r"C:\giwanos"
DB=os.environ.get("VELOS_DB_PATH", os.path.join(ROOT, "data", "velos.db"))

def open_db(path):
    c=sqlite3.connect(path, timeout=5, isolation_level=None)
    c.execute("PRAGMA journal_mode=WAL;")
    c.execute("PRAGMA synchronous=NORMAL;")
    c.execute("PRAGMA busy_timeout=5000;")
    c.execute("PRAGMA foreign_keys=ON;")
    return c

def fts_exists(cur, q):
    return cur.execute("SELECT 1 FROM memory_fts WHERE memory_fts MATCH ? LIMIT 1", (q,)).fetchone() is not None

def main():
    con=open_db(DB); cur=con.cursor()
    cur.execute("BEGIN IMMEDIATE;")
    try:
        cur.execute("CREATE TEMP TABLE _smoke(ids integer);")
        cur.execute("INSERT INTO memory(ts, role, insight, raw) VALUES (strftime('%s','now'), 'test', 'alpha smoke', 'raw0');")
        rid = cur.execute("SELECT last_insert_rowid()").fetchone()[0]
        cur.execute("INSERT INTO _smoke VALUES (?)", (rid,))
        con.commit()
    except Exception:
        con.rollback(); raise

    ins = 1 if fts_exists(cur, "alpha") else 0
    cur.execute("UPDATE memory SET insight='beta smoke' WHERE id=(SELECT ids FROM _smoke LIMIT 1)")
    time.sleep(0.05)
    upd = 1 if fts_exists(cur, "beta") else 0
    alpha_after = 1 if fts_exists(cur, "alpha") else 0
    cur.execute("DELETE FROM memory WHERE id=(SELECT ids FROM _smoke LIMIT 1)")
    time.sleep(0.05)
    after_del = 1 if fts_exists(cur, "beta") else 0
    print(f"insert={ins} update(beta)={upd} alpha_after_update={alpha_after} after_delete={after_del}")

if __name__=="__main__":
    main()
