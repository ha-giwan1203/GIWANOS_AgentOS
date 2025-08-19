# [ACTIVE] VELOS FTS E2E Test
import sqlite3, time, os
db=r"C:\giwanos\data\velos.db"
con=sqlite3.connect(db, isolation_level=None); c=con.cursor()
c.execute("INSERT INTO memory(ts,role,insight,raw) VALUES (strftime('%s','now'),'probe','e2e probe token','raw')")
rid=c.execute("SELECT last_insert_rowid()").fetchone()[0]
n=c.execute("SELECT COUNT(*) FROM memory_fts WHERE memory_fts MATCH 'probe'").fetchone()[0]
assert n>0, f"Expected >0 hits for 'probe', got {n}"
c.execute("UPDATE memory SET insight='e2e beta token' WHERE id=?",(rid,)); time.sleep(0.05)
assert not c.execute("SELECT 1 FROM memory_fts WHERE rowid=? AND memory_fts MATCH 'probe' LIMIT 1",(rid,)).fetchone()
assert     c.execute("SELECT 1 FROM memory_fts WHERE rowid=? AND memory_fts MATCH 'beta'  LIMIT 1",(rid,)).fetchone()
c.execute("DELETE FROM memory WHERE id=?",(rid,)); time.sleep(0.05)
assert not c.execute("SELECT 1 FROM memory_fts WHERE rowid=? AND memory_fts MATCH 'beta'  LIMIT 1",(rid,)).fetchone()
print("fts_e2e: OK")
con.close()


