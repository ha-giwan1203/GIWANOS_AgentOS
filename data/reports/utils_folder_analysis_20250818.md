# VELOS utils 폴더 분석 리포트

**생성일**: 2025-08-18  
**분석자**: VELOS 시스템  
**목적**: utils 폴더 정리 및 VELOS 규칙 준수

## 📊 의존성 분석 결과

### 🔗 현재 사용 중인 파일들 (이동 불가)

#### 1. `utils/net.py` - 네트워크 유틸리티
- **사용 위치**: 6개 파일에서 import
  - `scripts/dispatch_slack.py`
  - `scripts/dispatch_report.py` 
  - `scripts/dispatch_push.py`
  - `scripts/dispatch_notion.py`
  - `scripts/notion_memory_page.py`
  - `scripts/notion_memory_db.py`
- **기능**: HTTP 요청 재시도 로직, 연결성 확인
- **상태**: ✅ **활성 사용 중** - 이동 불가

#### 2. `utils/utf8_force.py` - UTF-8 인코딩 설정
- **사용 위치**: 4개 파일에서 import
  - `dashboard/app.py`
  - `scripts/velos_dashboard.py`
  - `scripts/check_env.py`
- **기능**: UTF-8 인코딩 강제 설정
- **상태**: ✅ **활성 사용 중** - 이동 불가

#### 3. `utils/memory_adapter.py` - 메모리 어댑터 Shim
- **사용 위치**: 2개 파일에서 import
  - `modules/memory/router/velos_router_adapter.py`
  - `modules/core/context_builder.py`
- **기능**: modules.core.memory_adapter의 Shim 역할
- **상태**: ✅ **활성 사용 중** - 이동 불가

### 🗂️ 이동 가능한 파일들

#### 1. `utils/safe_math.py` - 안전한 수학 연산
- **사용 위치**: 없음
- **기능**: 0으로 나누기 방지, 안전한 수학 함수
- **권장 위치**: `modules/utils/` 또는 `modules/core/`

#### 2. `utils/load_env.py` - 환경 변수 로더
- **사용 위치**: 없음
- **기능**: 가상환경 .env 파일 로드
- **권장 위치**: `modules/utils/` 또는 `configs/`

#### 3. `utils/check_views.py` - 데이터베이스 뷰 확인
- **사용 위치**: 없음
- **기능**: SQLite 뷰/테이블 목록 확인
- **권장 위치**: `scripts/db_migrations/` 또는 `tools/`

#### 4. `utils/queue_jobs.py` - 작업 큐 테스트
- **사용 위치**: 없음
- **기능**: job_queue 테이블에 테스트 데이터 삽입
- **권장 위치**: `scripts/` 또는 `tests/`

#### 5. `utils/query_test.py` - 쿼리 테스트
- **사용 위치**: 없음
- **기능**: memory_roles 테이블 쿼리 테스트
- **권장 위치**: `tests/` 또는 `scripts/`

#### 6. `utils/quick_test_monitor_utils.py` - 모니터 유틸 테스트
- **사용 위치**: 없음
- **기능**: monitor_utils.py 자가 테스트
- **권장 위치**: `tests/` 또는 `scripts/`

## 🎯 정리 계획

### Phase 1: 이동 가능한 파일들 정리
1. **`modules/utils/` 폴더 생성**
2. **`safe_math.py` → `modules/utils/safe_math.py`**
3. **`load_env.py` → `modules/utils/load_env.py`**

### Phase 2: 테스트 파일들 정리
1. **`check_views.py` → `scripts/db_migrations/check_views.py`**
2. **`queue_jobs.py` → `scripts/queue_jobs.py`**
3. **`query_test.py` → `tests/test_memory_queries.py`**
4. **`quick_test_monitor_utils.py` → `tests/test_monitor_utils.py`**

### Phase 3: 활성 파일들 유지
- **`net.py`**: 현재 위치 유지 (의존성 많음)
- **`utf8_force.py`**: 현재 위치 유지 (의존성 많음)
- **`memory_adapter.py`**: 현재 위치 유지 (Shim 역할)

## ⚠️ 주의사항

1. **VELOS 규칙 준수**: "파일명 절대 변경 금지"
2. **의존성 보존**: 활성 사용 중인 파일은 이동하지 않음
3. **점진적 정리**: 한 번에 하나씩 이동하여 테스트
4. **백업 생성**: 이동 전 스냅샷 생성

## 📋 실행 체크리스트

- [ ] `modules/utils/` 폴더 생성
- [ ] `safe_math.py` 이동 및 테스트
- [ ] `load_env.py` 이동 및 테스트
- [ ] 테스트 파일들 이동
- [ ] 의존성 재확인
- [ ] 전체 시스템 테스트
- [ ] 최종 리포트 생성

---
**VELOS 운영 철학**: "판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다."








