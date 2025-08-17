-- VELOS 호환성 뷰
-- 기존 스크립트들이 새로운 memory 스키마와 호환되도록 매핑

CREATE VIEW IF NOT EXISTS memory_compat AS
SELECT
  id, ts,
  role AS "from",          -- 과거 스크립트 호환 (role을 from으로 매핑)
  role AS source,          -- role을 source로도 매핑
  insight AS text,         -- insight를 text로 매핑
  raw AS meta              -- raw를 meta로 매핑
FROM memory;

CREATE VIEW IF NOT EXISTS memory_roles AS
SELECT
  m.id, m.ts,
  COALESCE(
    CASE WHEN m.role IN ('user','system','assistant','test') THEN m.role END,
    'unknown'
  ) AS role,
  m.role AS source,
  m.insight AS text,
  m.raw AS meta
FROM memory m;

-- 통합된 역할별 쿼리를 위한 새로운 뷰
CREATE VIEW IF NOT EXISTS memory_roles_unified AS
SELECT
  m.id, m.ts,
  COALESCE(
    CASE WHEN m.role IN ('user','system','assistant','test') THEN m.role END,
    'unknown'
  ) AS role,
  m.role AS source,
  m.insight AS text,
  m.raw AS meta,
  CASE
    WHEN m.role IN ('user', 'system') THEN 1
    ELSE 0
  END AS is_primary_role
FROM memory m
WHERE m.role IN ('user', 'system', 'assistant', 'test');

-- FTS 검색을 위한 텍스트 뷰
CREATE VIEW IF NOT EXISTS memory_text AS
SELECT
  m.id, m.ts,
  m.role,
  m.role AS "from",
  m.insight AS text_norm,
  m.raw,
  m.tags
FROM memory m
WHERE m.insight IS NOT NULL AND m.insight != '';
