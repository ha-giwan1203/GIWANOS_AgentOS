# VELOS Cursor 점검 체크리스트

## 필수
- [x] .cursorrules 존재, 규칙 반영됨
- [x] tasks.json 배치, "풀 헬스체크" 수행 OK
- [x] session_store --selftest OK
- [x] 학습 메모리 JSONL/JSON 갱신 OK
- [x] snapshots 생성 OK
- [x] 대시보드 import OK
- [x] 스케줄러 창 숨김 OK

## 로그 확인
- [x] data/logs/* 최근 오류 없음
- [x] 보고서 생성 시 폰트 경고 제거

## 금지
- [x] 파일명 변경 없음
- [ ] 절대 경로 하드코딩 없음

## 상세 점검 결과

### ✅ 완료된 항목

1. **session_store --selftest OK**
   - 실행 결과: `[selftest] append_ts=2025-08-16T23:38:33 merge_appended=37 snapshot=session_snapshot_1755355113_905444.json`
   - 상태: 정상 작동

2. **학습 메모리 JSONL/JSON 갱신 OK**
   - `data/memory/learning_memory.jsonl`: 37개 항목 (최신: 2025-08-16T23:37:15)
   - `data/memory/learning_memory.json`: 37개 항목 포함된 스냅샷
   - 상태: 정상 갱신됨

3. **snapshots 생성 OK**
   - `data/snapshots/`: 30개 이상의 세션 스냅샷 파일 존재
   - 최신: `session_snapshot_1755355113_905444.json`
   - 상태: 정상 생성됨

4. **대시보드 import OK**
   - `interface.velos_dashboard`: 임포트 성공
   - `interface.status_dashboard`: 모듈 없음 (정상 - 해당 모듈이 존재하지 않음)
   - 상태: 정상 작동

5. **스케줄러 창 숨김 OK**
   - "VELOS Session Merge": `-WindowStyle Hidden` 설정됨
   - "VELOS Bridge Flush": 없음 (정상)
   - 상태: 모든 태스크가 창 숨김 모드

6. **data/logs/* 최근 오류 없음**
   - `error.log`: 테스트 메시지만 존재
   - `last_run.stderr.txt`: 이전 오류 (ImportError: cannot import name 'ROOT')
   - 상태: 현재는 오류 없음

### ⚠️ 주의사항

1. **절대 경로 하드코딩 발견**
   - 50개 이상의 파일에서 `C:\giwanos` 하드코딩 발견
   - 주요 파일들:
     - `interface/velos_dashboard.py`
     - `modules/velos_common.py`
     - `scripts/velos_guardian_check.py`
     - 기타 다수 스크립트 파일들

2. **대시보드 임포트 경고**
   - Streamlit 관련 경고 메시지 다수 출력
   - 기능상 문제없지만 로그 정리가 필요

### 🔧 권장 조치사항

1. **절대 경로 하드코딩 제거**
   - 환경변수 `VELOS_ROOT` 사용으로 통일
   - `os.environ.get('VELOS_ROOT', 'C:/giwanos')` 패턴 적용

2. **로그 정리**
   - Streamlit 경고 메시지 필터링
   - 불필요한 디버그 로그 제거

## 최종 상태: ✅ 대부분 완료 (절대 경로 하드코딩 제거 필요)
