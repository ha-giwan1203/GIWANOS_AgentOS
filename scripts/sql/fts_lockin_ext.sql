BEGIN IMMEDIATE;

-- 안전 정리
DROP TRIGGER IF EXISTS trg_mem_ai;
DROP TRIGGER IF EXISTS trg_mem_au;
DROP TRIGGER IF EXISTS trg_mem_ad;
DROP TRIGGER IF EXISTS trg_mem_bu;
DROP TRIGGER IF EXISTS trg_mem_bd;
DROP TABLE   IF EXISTS memory_fts;

-- 외부컨텐츠 FTS 테이블
CREATE VIRTUAL TABLE memory_fts USING fts5(
  insight, raw,
  content='memory',
  content_rowid='id',
  tokenize='unicode61',
  prefix='2 3 4'
);

-- INSERT: 신규 인덱싱
CREATE TRIGGER trg_mem_ai AFTER INSERT ON memory BEGIN
  INSERT INTO memory_fts(rowid, insight, raw)
  VALUES (new.id, new.insight, new.raw);
END;

-- UPDATE: 변경 전 기존 인덱스 제거
CREATE TRIGGER trg_mem_bu BEFORE UPDATE OF insight, raw ON memory BEGIN
  DELETE FROM memory_fts WHERE rowid = old.id;
END;

-- UPDATE: 변경 후 신규 인덱싱
CREATE TRIGGER trg_mem_au AFTER  UPDATE OF insight, raw ON memory BEGIN
  INSERT INTO memory_fts(rowid, insight, raw)
  VALUES (new.id, new.insight, new.raw);
END;

-- DELETE: 삭제 직전 인덱스 제거
CREATE TRIGGER trg_mem_bd BEFORE DELETE ON memory BEGIN
  DELETE FROM memory_fts WHERE rowid = old.id;
END;

-- 초기 재색인 + 최적화
DELETE FROM memory_fts;
INSERT INTO memory_fts(rowid, insight, raw)
  SELECT id, insight, raw FROM memory;
INSERT INTO memory_fts(memory_fts) VALUES('optimize');

COMMIT;
