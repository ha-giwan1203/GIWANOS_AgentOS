# VELOS Memory System - SQLite FTS5 확장 및 JSONL 수집

## 개요

VELOS 시스템의 메모리 저장소를 SQLite FTS5를 이용해 확장하고, JSONL 파일 수집 기능, TTL 기반 캐시 시스템, 스마트 쿼리 라우팅, 자동 캐시 무효화를 추가한 통합 모듈입니다.

## 주요 기능

### 1. FTS5 전체 텍스트 검색
- SQLite FTS5 가상 테이블을 이용한 고성능 검색
- 한국어 토큰화 지원 (unicode61)
- insight와 raw 필드 모두 검색 가능

### 2. 크로스프로세스 락
- SQLite 테이블 기반 advisory lock
- TTL 기반 자동 만료
- 동시성 제어 보장

### 3. 기존 시스템 호환성
- 기존 VELOS MemoryAdapter와 완전 호환
- 기존 스키마 유지 (role, insight, raw, tags)
- 점진적 마이그레이션 지원

### 4. JSONL 파일 수집
- 다양한 JSONL 파일 형식 지원
- UTF-8 BOM 자동 처리
- 레코드 정규화 및 중복 방지
- 크로스프로세스 락으로 안전한 수집

### 5. 메모리 캐시 시스템
- TTL 기반 LRU 캐시
- 검색 결과 캐싱으로 성능 향상
- 자동 캐시 무효화
- 캐시 통계 및 모니터링

### 6. 스마트 쿼리 라우팅
- 쿼리 타입 자동 감지 (키워드 vs 긴 쿼리)
- 최근 N일 우선 검색으로 성능 최적화
- FTS5 + LIKE 하이브리드 검색
- BM25 점수 기반 정확도 순 정렬

### 7. 자동 캐시 무효화
- 데이터베이스 버전 변경 감지
- PRAGMA data_version 기반 자동 무효화
- 데이터 일관성 보장
- 성능과 정확도 균형 유지

## 파일 구조

```
modules/memory/
├── storage/
│   ├── sqlite_store.py      # 핵심 SQLite 저장소
│   ├── velos_adapter.py     # 기존 시스템 통합 어댑터
│   └── README.md           # 이 파일
├── ingest/
│   └── jsonl_ingest.py     # JSONL 파일 수집 모듈
├── cache/
│   ├── memory_cache.py      # TTL 기반 메모리 캐시
│   └── velos_cache_adapter.py # 캐시 통합 어댑터
└── router/
    ├── query_router.py      # 스마트 쿼리 라우팅
    └── velos_router_adapter.py # 라우터 통합 어댑터
```

## 사용법

### 기본 사용법

```python
from modules.memory.storage.sqlite_store import VelosMemoryStore

# 컨텍스트 매니저로 사용
with VelosMemoryStore() as store:
    # 메모리 삽입
    memory_id = store.insert_memory(
        ts=int(time.time()),
        role="user",
        insight="VELOS 운영 철학",
        raw="파일명 불변, 자가 검증 원칙",
        tags=["philosophy", "velos"]
    )

    # FTS 검색
    results = store.search_fts("VELOS", limit=10)

    # 최근 메모리 조회
    recent = store.get_recent(limit=20)
```

### 기존 시스템과 통합

```python
from modules.memory.storage.velos_adapter import VelosEnhancedMemoryAdapter

# 기존 MemoryAdapter의 모든 기능 + 새로운 기능
adapter = VelosEnhancedMemoryAdapter()

# 기존 기능
adapter.append_jsonl(item)
adapter.flush_jsonl_to_db()

# 새로운 기능
fts_results = adapter.search_fts("검색어")
enhanced_stats = adapter.get_stats_enhanced()
memory_id = adapter.insert_direct(ts, role, insight, raw, tags)
```

### 캐시 시스템 사용

```python
from modules.memory.cache.velos_cache_adapter import VelosCachedMemoryAdapter

# 캐시가 통합된 어댑터
cached_adapter = VelosCachedMemoryAdapter()

# 캐시된 검색 (성능 향상)
results = cached_adapter.search_fts_cached("검색어", limit=10)

# 캐시된 최근 조회
recent = cached_adapter.get_recent_cached(limit=20)

# 캐시 통계 확인
cache_stats = cached_adapter.get_cache_stats()

# 캐시 무효화
cached_adapter.invalidate_search_cache()
```

### 스마트 라우팅 사용

```python
from modules.memory.router.velos_router_adapter import VelosRouterMemoryAdapter

# 스마트 라우팅이 통합된 어댑터
router_adapter = VelosRouterMemoryAdapter()

# 스마트 검색 (쿼리 타입 자동 감지)
results = router_adapter.smart_search("VELOS", limit=10)

# 고급 검색 (기간, 제한 설정)
results = router_adapter.advanced_search("검색", days=7, limit=20)

# 역할별 검색
user_results = router_adapter.search_by_role("user", limit=10)

# 최근 검색
recent_results = router_adapter.search_recent_by_days(1, limit=10)

# 종합 통계
stats = router_adapter.get_comprehensive_stats()

## 스키마

### 메모리 테이블 (기존 호환)
```sql
CREATE TABLE memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER NOT NULL,
    role TEXT NOT NULL,         -- 'user' | 'system' 등
    insight TEXT NOT NULL,      -- 요약/인사이트
    raw TEXT,                   -- 원문(raw)
    tags TEXT                   -- JSON array string
);
```

### FTS5 가상 테이블
```sql
CREATE VIRTUAL TABLE memory_fts USING fts5(
    insight, raw, content='memory', content_rowid='id', tokenize='unicode61'
);
```

### 락 테이블
```sql
CREATE TABLE locks(
    name TEXT PRIMARY KEY,
    owner TEXT NOT NULL,
    ts INTEGER NOT NULL
);
```

## 표준 FTS5 스키마

VELOS 시스템의 전체 텍스트 검색을 위한 표준 `memory_fts` 스키마:

```sql
CREATE VIRTUAL TABLE memory_fts USING fts5(
    insight, raw, content='memory', content_rowid='id', tokenize='unicode61'
)
```

### 컬럼 설명
- `insight`: 메모리의 핵심 인사이트 텍스트
- `raw`: 원본 데이터 또는 추가 컨텍스트
- `content='memory'`: 외부 테이블 참조
- `content_rowid='id'`: 외부 테이블의 행 ID 매핑
- `tokenize='unicode61'`: 유니코드 토크나이저 사용

### 트리거
```sql
-- INSERT 트리거
CREATE TRIGGER trg_mem_ai AFTER INSERT ON memory BEGIN
    INSERT INTO memory_fts(rowid, insight, raw) VALUES (new.id, new.insight, new.raw);
END;

-- DELETE 트리거
CREATE TRIGGER trg_mem_ad AFTER DELETE ON memory BEGIN
    INSERT INTO memory_fts(memory_fts, rowid, insight, raw) VALUES('delete', old.id, old.insight, old.raw);
END;

-- UPDATE 트리거
CREATE TRIGGER trg_mem_au AFTER UPDATE ON memory BEGIN
    INSERT INTO memory_fts(memory_fts, rowid, insight, raw) VALUES('delete', old.id, old.insight, old.raw);
    INSERT INTO memory_fts(rowid, insight, raw) VALUES (new.id, new.insight, new.raw);
END;
```

## 성능 최적화

- WAL 모드 활성화
- 메모리 매핑 (256MB)
- 비동기 커밋
- 인덱스 최적화

## 자가 검증

각 모듈은 자가 검증 기능을 포함합니다:

```bash
# SQLite 저장소 테스트
python modules/memory/storage/sqlite_store.py

# 통합 어댑터 테스트
python modules/memory/storage/velos_adapter.py

# JSONL 수집 테스트
python modules/memory/ingest/jsonl_ingest.py --test

# 실제 JSONL 수집
python modules/memory/ingest/jsonl_ingest.py

# 캐시 테스트
python modules/memory/cache/memory_cache.py

# 캐시 어댑터 테스트
python modules/memory/cache/velos_cache_adapter.py

# 쿼리 라우터 테스트
python modules/memory/router/query_router.py

# 라우터 어댑터 테스트
python modules/memory/router/velos_router_adapter.py

# FTS 테스트 스크립트
python scripts/test_fts.py
python scripts/test_fts_comprehensive.py

# 캐시 무효화 테스트
python scripts/test_cache_invalidation.py
```

## 테스트 스크립트

### 기본 FTS 테스트
```bash
python scripts/test_fts.py
```
- 기본 검색 기능 테스트
- 고급 검색 기능 테스트
- 캐시 통계 확인

### 종합 FTS 테스트
```bash
python scripts/test_fts_comprehensive.py
```
- 성능 테스트 (캐시 효과 측정)
- 캐시 동작 테스트
- 종합 통계 수집
- 시스템 상태 모니터링

### 캐시 무효화 테스트
```bash
python scripts/test_cache_invalidation.py
```
- 자동 캐시 무효화 기능 테스트
- 데이터베이스 변경 감지 검증
- 캐시 일관성 확인
- 다중 무효화 시나리오 테스트

## 워크플로우 실행

### 환경 변수 설정
```powershell
# PowerShell에서 실행
powershell -ExecutionPolicy Bypass -File scripts/setup_velos_env.ps1
```

### 전체 워크플로우 실행
```powershell
# PowerShell에서 실행
powershell -ExecutionPolicy Bypass -File scripts/run_velos_workflow.ps1
```

### 수동 실행 순서
```bash
# 1. 환경 변수 설정
$env:VELOS_ROOT = "C:\giwanos"
$env:VELOS_DB = "C:\giwanos\data\velos.db"
$env:VELOS_JSONL_DIR = "C:\giwanos\data\memory"

# 2. 스키마/DB 초기화 (ingest 자동 수행)
python -m modules.memory.ingest.jsonl_ingest

# 3. 회수 품질 테스트
python scripts/test_fts.py
```

## VELOS 운영 철학 준수

- ✅ 파일명 절대 변경 금지
- ✅ VELOS 운영 철학 선언문 포함
- ✅ 환경 변수 우선순위 로딩
- ✅ 자가 검증 필수
- ✅ 한국어 응답
- ✅ 기존 시스템 호환성 유지
