BEGIN IMMEDIATE;
DROP TRIGGER IF EXISTS trg_mem_ai;
DROP TRIGGER IF EXISTS trg_mem_au;
DROP TRIGGER IF EXISTS trg_mem_ad;

-- INSERT: 새 문서 인덱싱
CREATE TRIGGER trg_mem_ai AFTER INSERT ON memory BEGIN
  INSERT INTO memory_fts(rowid, insight, raw)
  VALUES (new.id, new.insight, new.raw);
END;

-- UPDATE: 기존 토큰 tombstone 후 신규 토큰 인덱싱
-- insight/raw 바뀔 때만 작동하도록 명시
CREATE TRIGGER trg_mem_au AFTER UPDATE OF insight, raw ON memory BEGIN
  INSERT INTO memory_fts(memory_fts, rowid) VALUES('delete', old.id);
  INSERT INTO memory_fts(rowid, insight, raw)
  VALUES (new.id, new.insight, new.raw);
END;

-- DELETE: tombstone
CREATE TRIGGER trg_mem_ad AFTER DELETE ON memory BEGIN
  INSERT INTO memory_fts(memory_fts, rowid) VALUES('delete', old.id);
END;
COMMIT;
