-- VELOS FTS 호환성 뷰 드롭 스크립트
-- 해당 날짜(2025-10-19) 이후에 실행

BEGIN IMMEDIATE;

-- 구식 호환성 뷰들 제거
DROP VIEW IF EXISTS memory_fts_text;
DROP VIEW IF EXISTS memory_fts_compat;

-- 변경사항 확인
SELECT name FROM sqlite_master WHERE type='view' AND name LIKE 'memory_fts%';

COMMIT;
