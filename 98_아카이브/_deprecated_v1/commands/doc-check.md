> 슬래시 커맨드 `/doc-check` 및 `Skill(skill="doc-check")` 공통 지시문

# 문서 정합성 검사

아래 순서로 프로젝트 상태 문서의 정합성을 검사하고 결과를 보고하세요.

## 검사 대상
1. `90_공통기준/업무관리/TASKS.md` — 상태 원본 (1순위)
2. `90_공통기준/업무관리/STATUS.md` — 운영 요약
3. `90_공통기준/업무관리/HANDOFF.md` — 세션 메모
4. 도메인 `STATUS.md` 파일들 (`05_생산실적/조립비정산/STATUS.md`, `10_라인배치/STATUS.md`)

## 검사 항목

### 1. TASKS.md 내부 정합성
- 진행 중 항목이 1개 이하인지 확인
- 완료 항목에 날짜가 있는지 확인
- 대기 항목의 상태(대기/차단/보류)가 명확한지 확인

### 2. TASKS ↔ STATUS 충돌
- STATUS.md의 재개 위치가 TASKS.md 상태와 일치하는지
- STATUS.md에서 "완료"라고 언급한 것이 TASKS.md에서도 완료인지
- 도메인 STATUS.md의 재개점이 TASKS.md와 충돌하지 않는지

### 3. TASKS ↔ HANDOFF 충돌
- HANDOFF.md의 "다음 AI 할 일"이 TASKS.md 대기 항목과 일치하는지
- HANDOFF.md에서 완료라고 선언한 것이 TASKS.md에서도 완료인지

### 4. 날짜 정합성
- 각 문서의 "최종 업데이트" 날짜가 최근 커밋 날짜와 대략 일치하는지

## 출력 형식
각 검사 항목별로 PASS / FAIL / WARNING 판정.
FAIL이 있으면 어떤 문서의 어떤 줄이 충돌하는지 구체적으로 표시.
