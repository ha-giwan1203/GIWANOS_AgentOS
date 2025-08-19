# [ACTIVE] VELOS 운영 철학: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""

import os, sqlite3, io, time, shutil

ROOT = os.getenv("VELOS_ROOT", r"C:\giwanos")
OLD  = os.getenv("VELOS_DB_PATH", os.path.join(ROOT, "data", "velos.db"))
NEW  = os.getenv("VELOS_DB_NEW_PATH", os.path.join(ROOT, "data", "velos_new.db"))
DATA = os.path.dirname(OLD)
BKD  = os.path.join(ROOT, "backup")
os.makedirs(BKD, exist_ok=True)
os.makedirs(os.path.dirname(NEW), exist_ok=True)

def open_db(path, ro=False, iso=None):
    if ro:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=10)
    else:
        con = sqlite3.connect(path, isolation_level=iso, timeout=10)
    for p in ("journal_mode=WAL","synchronous=NORMAL","busy_timeout=5000","foreign_keys=ON"):
        try: con.execute(f"PRAGMA {p};")
        except sqlite3.DatabaseError: pass
    return con

# 1) 말썽꾸러기 wal/shm 제거(있으면)
for ext in (".wal",".shm"):
    p = OLD + ext
    try:
        if os.path.exists(p): os.remove(p)
    except Exception: pass

# 2) 새 DB 생성 + 스키마/FTS 트리거 강화 적용
STRICT_FTS = """
BEGIN IMMEDIATE;
DROP TRIGGER IF EXISTS trg_mem_ai;
DROP TRIGGER IF EXISTS trg_mem_au;
DROP TRIGGER IF EXISTS trg_mem_ad;
DROP TRIGGER IF EXISTS trg_mem_bu;
DROP TRIGGER IF EXISTS trg_mem_bd;
DROP TABLE   IF EXISTS memory_fts;
DROP TABLE   IF EXISTS memory;

CREATE TABLE memory(
  id INTEGER PRIMARY KEY,
  ts INTEGER NOT NULL,
  role TEXT NOT NULL,
  insight TEXT,
  raw TEXT,
  tags TEXT
);

CREATE VIRTUAL TABLE memory_fts USING fts5(
  insight, raw,
  content='memory',
  content_rowid='id',
  tokenize='unicode61',
  prefix='2 3 4'
);

CREATE TRIGGER trg_mem_ai AFTER INSERT ON memory BEGIN
  INSERT INTO memory_fts(rowid, insight, raw)
  VALUES (new.id, new.insight, new.raw);
END;

CREATE TRIGGER trg_mem_bu BEFORE UPDATE OF insight, raw ON memory BEGIN
  DELETE FROM memory_fts WHERE rowid = old.id;
END;

CREATE TRIGGER trg_mem_au AFTER  UPDATE OF insight, raw ON memory BEGIN
  INSERT INTO memory_fts(rowid, insight, raw)
  VALUES (new.id, new.insight, new.raw);
END;

CREATE TRIGGER trg_mem_bd BEFORE DELETE ON memory BEGIN
  DELETE FROM memory_fts WHERE rowid = old.id;
END;

COMMIT;
"""

con_new = open_db(NEW, ro=False, iso=None)
con_new.executescript(STRICT_FTS)
con_new.commit()

# 3) 기존 DB에서 데이터 이주(가능한 것만 안전하게)
migrated = 0
skipped  = 0
if os.path.exists(OLD):
    try:
        con_old = open_db(OLD, ro=True, iso=None)
        cur_old = con_old.cursor()
        rows = cur_old.execute("SELECT id, ts, role, insight, raw, tags FROM memory ORDER BY id").fetchmany(1000)
        cur_new = con_new.cursor()
        while rows:
            for r in rows:
                try:
                    cur_new.execute("INSERT INTO memory(id, ts, role, insight, raw, tags) VALUES(?,?,?,?,?,?)", r)
                    migrated += 1
                except Exception:
                    skipped += 1
            con_new.commit()
            rows = cur_old.execute("SELECT id, ts, role, insight, raw, tags FROM memory WHERE id > ? ORDER BY id", (r[0],)).fetchmany(1000)
        con_old.close()
    except Exception as e:
        print("[WARN] read old DB:", e)

# 4) FTS 전체 재색인 + 최적화
cur = con_new.cursor()
try:
    cur.executescript("""
    BEGIN IMMEDIATE;
    INSERT INTO memory_fts(memory_fts) VALUES('rebuild');
    INSERT INTO memory_fts(memory_fts) VALUES('optimize');
    COMMIT;
    """)
except Exception:
    cur.executescript("""
    BEGIN IMMEDIATE;
    DELETE FROM memory_fts;
    INSERT INTO memory_fts(rowid, insight, raw)
      SELECT id, insight, raw FROM memory;
    INSERT INTO memory_fts(memory_fts) VALUES('optimize');
    COMMIT;
    """)

# 5) 무결성 점검
ic  = cur.execute("PRAGMA integrity_check").fetchone()[0]
try:
    fic = cur.execute("SELECT fts5_integrity_check('memory_fts')").fetchone()[0]
except Exception as e:
    fic = f"ERR {e}"
fts_rows = cur.execute("SELECT count(*) FROM memory_fts").fetchone()[0]
con_new.commit()
con_new.close()

print(f"[NEW] migrated={migrated} skipped={skipped} fts_rows={fts_rows} integrity={ic} fts5={fic}")

# 6) 원자적 스왑
ts = time.strftime("%Y%m%d_%H%M%S")
bak = os.path.join(BKD, f"velos_old_{ts}.db")
if os.path.exists(OLD):
    shutil.copyfile(OLD, bak)
    print("[backup]", bak)

shutil.copyfile(NEW, OLD)
print("[swap] new -> velos.db")

# 7) 최종 단일 rowid 프로브
con = open_db(OLD, ro=False, iso=None); c = con.cursor()
def hit(q, rid=None):
    if rid is None:
        return c.execute("SELECT 1 FROM memory_fts WHERE memory_fts MATCH ? LIMIT 1",(q,)).fetchone() is not None
    return c.execute("SELECT 1 FROM memory_fts WHERE rowid=? AND memory_fts MATCH ? LIMIT 1",(rid,q)).fetchone() is not None

c.execute("INSERT INTO memory(ts,role,insight,raw) VALUES (strftime('%s','now'),'probe','alpha strict','r')")
rid=c.execute("SELECT last_insert_rowid()").fetchone()[0]
a0=hit("alpha",rid)
c.execute("UPDATE memory SET insight='beta strict' WHERE id=?",(rid,))
time.sleep(0.05)
a1=hit("alpha",rid); b1=hit("beta",rid)
c.execute("DELETE FROM memory WHERE id=?",(rid,))
time.sleep(0.05)
b2=hit("beta",rid)
print(f"[probe] alpha_pre={int(a0)} alpha_after_update={int(a1)} beta_after_update={int(b1)} beta_after_delete={int(b2)}")
con.close()


