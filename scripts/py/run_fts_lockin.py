# [ACTIVE] FTS external-content lock-in 실행 스크립트
import os, sqlite3, io

ROOT = r"C:\giwanos"
DB = os.environ.get("VELOS_DB_PATH", os.path.join(ROOT, "data", "velos.db"))
SQL = os.path.join(ROOT, "scripts", "sql", "fts_lockin_ext.sql")

def main():
    if not os.path.exists(DB): raise SystemExit(f"DB not found: {DB}")
    if not os.path.exists(SQL): raise SystemExit(f"SQL not found: {SQL}")
    con=sqlite3.connect(DB, timeout=5)
    try:
        for p in ("journal_mode=WAL","synchronous=NORMAL","busy_timeout=5000","foreign_keys=ON"):
            con.execute(f"PRAGMA {p};")
        with open(SQL, "r", encoding="utf-8") as f:
            sql_content = f.read()
        con.executescript(sql_content)
        c=con.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='memory_fts'").fetchone()[0]
        if c!=1: raise RuntimeError("memory_fts not created")
        total=con.execute("SELECT count(*) FROM memory_fts").fetchone()[0]
        print(f"FTS external-content lock-in OK (rows={total})")
    finally:
        con.close()
if __name__=="__main__":
    main()


