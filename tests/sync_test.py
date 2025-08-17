import json, sqlite3, os, glob, sys
root=r"C:/giwanos"
jsonl=max(glob.glob(os.path.join(root,"data/memory/*.jsonl")), key=os.path.getmtime)
db=os.path.join(root,"data/memory/velos.db")
# JSONL 마지막 레코드 ts
last_line=""
with open(jsonl,"r",encoding="utf-8") as f:
    for last_line in f: pass
j=json.loads(last_line)
j_ts=j.get("ts") or j.get("timestamp")
# SQLite 마지막 레코드 ts
con=sqlite3.connect(db)
cur=con.execute("select ts from memory_events order by ts desc limit 1")
row=cur.fetchone(); con.close()
d_ts=row[0] if row else None
ok = bool(j_ts and d_ts and str(j_ts)==str(d_ts))
print(f"[SYNC] JSONL={jsonl} ts={j_ts} | DB={os.path.basename(db)} ts={d_ts} | SYNC_OK={ok}")
sys.exit(0 if ok else 2)
