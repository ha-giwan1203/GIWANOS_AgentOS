# TASKS-STATUS 충돌 탐지

TASKS.md와 모든 STATUS.md 파일 간의 상태 충돌을 자동 탐지하세요.

## 검사 절차

### Step 1: TASKS.md 파싱
- `90_공통기준/업무관리/TASKS.md` 읽기
- 진행 중 / 대기 중 / 완료 항목 분류
- 각 항목의 현재 상태 기록

### Step 2: STATUS.md 파일 수집
아래 경로의 STATUS.md를 모두 읽기:
- `90_공통기준/업무관리/STATUS.md`
- `05_생산실적/조립비정산/STATUS.md`
- `10_라인배치/STATUS.md`

### Step 3: 충돌 패턴 탐지

**패턴 A — 재개 위치 불일치**
STATUS.md에 "다음 재개: X" 또는 "재개 위치: X"가 있는데 TASKS.md에서 해당 작업이 완료/취소/차단 상태인 경우.

**패턴 B — 완료 선언 불일치**
STATUS.md에서 "완료" 언급이 있는데 TASKS.md에서 해당 항목이 아직 대기/진행 중인 경우.

**패턴 C — 날짜 역전**
STATUS.md 최종 업데이트 날짜가 TASKS.md보다 오래된 경우 (TASKS가 더 최신인데 STATUS가 갱신 안 됨).

**패턴 D — 유령 항목**
STATUS.md에서 언급하는 작업이 TASKS.md에 아예 없는 경우.

### Step 4: 결과 보고
충돌 건수, 각 충돌의 패턴 유형(A/B/C/D), 관련 파일과 줄 번호, 권장 수정 방향 제시.
충돌 없으면 "ALL CLEAR — 충돌 없음" 출력.
