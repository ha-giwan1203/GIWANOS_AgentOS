BEGIN IMMEDIATE;
DROP TRIGGER IF EXISTS trg_mem_ai;
DROP TRIGGER IF EXISTS trg_mem_au;
DROP TRIGGER IF EXISTS trg_mem_ad;
DROP TRIGGER IF EXISTS trg_mem_bu;
DROP TRIGGER IF EXISTS trg_mem_bd;

-- INSERT: 새 문서 인덱싱
CREATE TRIGGER trg_mem_ai AFTER INSERT ON memory BEGIN
  INSERT INTO memory_fts(rowid, insight, raw)
  VALUES (new.id, new.insight, new.raw);
END;

-- UPDATE: 업데이트 직전에 기존 토큰 완전 제거
CREATE TRIGGER trg_mem_bu BEFORE UPDATE OF insight, raw ON memory BEGIN
  DELETE FROM memory_fts WHERE rowid = old.id;
END;

-- UPDATE 후 신규 토큰 인덱싱
CREATE TRIGGER trg_mem_au AFTER UPDATE OF insight, raw ON memory BEGIN
  INSERT INTO memory_fts(rowid, insight, raw)
  VALUES (new.id, new.insight, new.raw);
END;

-- DELETE: 삭제 직전에 인덱스 제거
CREATE TRIGGER trg_mem_bd BEFORE DELETE ON memory BEGIN
  DELETE FROM memory_fts WHERE rowid = old.id;
END;
COMMIT;
