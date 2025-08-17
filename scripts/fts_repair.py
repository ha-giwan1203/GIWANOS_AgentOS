import os
import sqlite3

DB = os.getenv("VELOS_DB", r"C:\giwanos\data\velos.db")
con = sqlite3.connect(DB)
cur = con.cursor()


def cols(table):
    return [r[1] for r in cur.execute(
        f"PRAGMA table_info('{table}')").fetchall()]


mem_cols = cols('memory')  # 예: ['id','ts','role','insight','raw','tags']
fts_cols = cols('memory_fts')  # 예: ['text']

# 2) FTS 테이블을 표준 1컬럼(text)로 통일. 기존이 insight/raw면 드랍 후 재생성
if ('text' not in fts_cols) or (not fts_cols):
    cur.execute("DROP TABLE IF EXISTS memory_fts")
    cur.execute("CREATE VIRTUAL TABLE memory_fts USING fts5(text)")

# 3) 동기화 트리거를 메모리 스키마에 맞춰 재생성
cur.execute("DROP TRIGGER IF EXISTS trg_mem_ai")
cur.execute("DROP TRIGGER IF EXISTS trg_mem_ad")
cur.execute("DROP TRIGGER IF EXISTS trg_mem_au")

cur.execute("""CREATE TRIGGER IF NOT EXISTS trg_mem_ai
AFTER INSERT ON memory BEGIN
  INSERT INTO memory_fts(rowid, text) VALUES (new.id, COALESCE(new.insight, new.raw, ''));
END;""")

cur.execute("""CREATE TRIGGER IF NOT EXISTS trg_mem_ad
AFTER DELETE ON memory BEGIN
  INSERT INTO memory_fts(memory_fts, rowid, text)
  VALUES('delete', old.id, COALESCE(old.insight, old.raw, ''));
END;""")

cur.execute("""CREATE TRIGGER IF NOT EXISTS trg_mem_au
AFTER UPDATE ON memory BEGIN
  INSERT INTO memory_fts(memory_fts, rowid, text)
  VALUES('delete', old.id, COALESCE(old.insight, old.raw, ''));
  INSERT INTO memory_fts(rowid, text) VALUES (new.id, COALESCE(new.insight, new.raw, ''));
END;""")

# 4) 누락분 백필 (안전 패턴)
cur.execute("""INSERT INTO memory_fts(rowid, text)
SELECT id, COALESCE(insight, raw, '')
FROM memory
WHERE id NOT IN (SELECT rowid FROM memory_fts)""")

# 5) 최적화 및 결과 확인
cur.execute("INSERT INTO memory_fts(memory_fts) VALUES('optimize')")
total_mem = cur.execute("SELECT COUNT(*) FROM memory").fetchone()[0]
total_fts = cur.execute("SELECT COUNT(*) FROM memory_fts").fetchone()[0]
con.commit()
con.close()
print(f"[OK] FTS repaired. memory={total_mem}, fts={total_fts}")
