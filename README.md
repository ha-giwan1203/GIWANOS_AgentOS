# VELOS - Vector Enhanced Learning and Operations System

## VELOS 운영 철학 선언문
판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

## 의존성 핀

### SQLite 버전 요구사항
- **최소 버전**: SQLite 3.35.0+ (FTS5 지원)
- **권장 버전**: SQLite 3.40.0+ (BM25 함수 지원)
- **현재 테스트 환경**: SQLite 3.42.0
- **호환성**: fts5_integrity_check가 없는 빌드도 자동 폴백으로 지원

### Python 요구사항
- **Python**: 3.9+
- **주요 패키지**: sqlite3, pathlib, typing

## 검색 품질 메트릭

### 성능 지표
- **search.qps**: 초당 검색 쿼리 수
- **search.latency_p50**: 검색 응답 시간 중간값 (밀리초)
- **fts.rebuild_count**: FTS 재색인 횟수

### 현재 기준값 (v2-fts-lockin)
- search.qps: > 1000/s
- search.latency_p50: < 50ms
- fts.rebuild_count: < 1/주

## 장애 퀵런북

### 6줄 복구 절차
```bash
# 1. 헬스체크
python scripts\py\fts_healthcheck.py

# 2. 실패시 긴급 복구
python scripts\py\fts_emergency_recovery.py

# 3. 재검증
python scripts\py\fts_healthcheck.py

# 4. 그래도 실패시 DB 재생성
python scripts\py\recreate_velos_db.py

# 5. 스모크 테스트
python scripts\py\fts_smoke_test.py
# 기대값: alpha_after_update=0, after_delete=0

# 6. 최악의 경우 골든 스냅샷 복원
# backup\velos_golden_*.db로 스왑
```

### 중요 규칙
- **CI/러너가 빨간불이면 배포 중단. 변명 금지.**
- **접두사 검색은 꼭 별(*) 붙인다**: `search_memory(cur, "deploy*")`
- **LIKE의 %는 금지**: FTS의 `term*` 패턴 사용

## E2E 테스트 예시
```python
# 호출부에서 접두사는 꼭 별(*) 붙인다
results = search_memory(cur, "deploy*")
assert isinstance(results, list)
```

## 설치 및 실행

### 환경 설정
```powershell
$env:VELOS_DB = "C:\giwanos\data\velos.db"
$env:VELOS_ROOT = "C:\giwanos"
```

### 검증 스위트
```powershell
python scripts\py\check_schema_guard.py
python scripts\py\fts_healthcheck.py
python scripts\py\fts_smoke_test.py
```

### 주간 유지보수
```powershell
powershell -ExecutionPolicy Bypass -File scripts\ps\fts_weekly_maintenance.ps1
```

## 릴리즈 정보

### v2-fts-lockin (2025-08-19)
- FTS5 검색 시스템 완전 고정
- 스키마 버전 2로 업그레이드
- 자동 복구 시스템 구현
- 주간 유지보수 스케줄러 등록
- 골든 스냅샷 보존: `backup/velos_golden_20250819_171455.db`

### v1.0-stable
- 초기 안정 버전

## 라이선스
MIT License
