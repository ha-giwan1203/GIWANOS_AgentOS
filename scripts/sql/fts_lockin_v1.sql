-- scripts/sql/fts_lockin_v1.sql

BEGIN IMMEDIATE;

-- 1) 표준 FTS 테이블 보장
DROP TABLE IF EXISTS memory_fts;
CREATE VIRTUAL TABLE memory_fts USING fts5(
  text,
  content='memory',
  content_rowid='id',
  tokenize='unicode61 remove_diacritics 2',
  prefix='2 3 4'
);

-- 2) 트리거 재정의 (기존 있으면 삭제 후 재생성)
DROP TRIGGER IF EXISTS trg_mem_ai;
DROP TRIGGER IF EXISTS trg_mem_ad;
DROP TRIGGER IF EXISTS trg_mem_au;

CREATE TRIGGER trg_mem_ai AFTER INSERT ON memory BEGIN
  INSERT INTO memory_fts(rowid, text)
  VALUES (new.id, COALESCE(new.insight, new.raw, ''));
END;

CREATE TRIGGER trg_mem_ad AFTER DELETE ON memory BEGIN
  INSERT INTO memory_fts(memory_fts, rowid, text)
  VALUES ('delete', old.id, COALESCE(old.insight, old.raw, ''));
END;

CREATE TRIGGER trg_mem_au AFTER UPDATE ON memory BEGIN
  INSERT INTO memory_fts(memory_fts, rowid, text)
  VALUES ('delete', old.id, COALESCE(old.insight, old.raw, ''));
  INSERT INTO memory_fts(rowid, text)
  VALUES (new.id, COALESCE(new.insight, new.raw, ''));
END;

-- 3) 호환 뷰 (이미 있으면 유지하거나 갈아끼우기)
DROP VIEW IF EXISTS memory_compat;
CREATE VIEW memory_compat AS
SELECT id, ts, role, COALESCE(insight, raw, '') AS text
FROM memory;

-- 4) 전체 재색인 + 최적화
DELETE FROM memory_fts;
INSERT INTO memory_fts(rowid, text)
SELECT id, COALESCE(insight, raw, '')
FROM memory
WHERE COALESCE(insight, raw, '') <> '';

INSERT INTO memory_fts(memory_fts) VALUES ('optimize');

COMMIT;
