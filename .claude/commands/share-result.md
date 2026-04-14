# GPT 결과 공유

커밋+푸시 완료 후 GPT 프로젝트방에 실물 결과를 자동 공유한다.
토론모드 CLAUDE.md "GPT 실물 검증 공유 규칙"을 자동 실행하는 명령이다.

## 실행 순서

### 1단계: 커밋+푸시 상태 확인 + 상태 문서 포함 검증
- `git status`로 미커밋 변경 확인
- 미커밋 변경이 있으면 커밋+푸시 먼저 진행 (사용자 확인 후)
- 이미 푸시 완료면 최신 커밋 SHA 수집
- **[필수] 상태 문서 포함 검증**: `git diff --name-only HEAD~1..HEAD`에서 TASKS.md 포함 여부 확인
  - TASKS.md 변경 없음 → **GPT 공유 진행 금지**. 먼저 TASKS.md에 해당 작업 상태를 갱신하고 커밋에 포함시킨다.
  - HANDOFF.md도 동일 기준 적용 (최신 세션 기록 확인)
  - 예외: docs/상태갱신 전용 커밋(TASKS/HANDOFF만 변경)은 이 검증 대상이 아님

### 2단계: 공유 내용 수집
- `git log --oneline -5`로 최근 커밋 SHA 수집
- 변경된 파일 경로 수집 (`git diff --name-only HEAD~N..HEAD`)
- TASKS.md에서 해당 작업 항목의 현재 상태 확인
- QA 결과가 있으면 포함

### 3~4단계: GPT 전송 (gpt-send 스킬 필수 호출)

**[MUST] 아래 형식으로 메시지를 조립한 뒤 반드시 `/gpt-send` 스킬을 호출한다.**
수동 탭 탐색·navigate·스크린샷·클릭으로 프로젝트방에 진입하는 것은 금지다.
프로젝트 진입~대화방 탐지~전송~응답 대기 전체를 `/gpt-send`가 처리한다.

```
Skill(skill="gpt-send", args="조립된 메시지 텍스트")
```

메시지 형식:
```
## 실물 결과 공유

### 커밋 이력
- {SHA}: {커밋 메시지}

### 변경 파일
- {파일 경로 목록}

### 현재 상태
- TASKS.md: {해당 항목 상태}

### 판정 요청
커밋 실물 확인 후 PASS/FAIL 판정 요청합니다.
GitHub: ha-giwan1203/GIWANOS_AgentOS main 브랜치.
```

**[NEVER]** tabs_context_mcp → navigate → screenshot → click 순서로 수동 진입 금지.
**[NEVER]** gpt-send 스킬 호출 전에 ChatGPT 탭을 먼저 열거나 탐색하는 행위 금지.

### 5단계: GPT 응답 대기 + 하네스 분석 + 지적사항 즉시 대응
- 적응형 polling으로 응답 대기
- 응답 수신 후 하네스 분석 (채택/보류/버림)
- **[필수] GPT 지적사항 즉시 행동**: GPT 응답에 문제 지적·개선 제안·불일치 발견이 포함되면:
  1. 읽기만 하고 넘어가지 않는다 — 지적 항목을 action item으로 추출
  2. 즉시 대응 가능한 건 → 바로 수정 + 재커밋 (FAIL 대기 없이 선제 대응)
  3. 판정과 무관한 관찰/제안 → TASKS.md 다음 의제로 기록
  4. "GPT가 먼저 발견한 문제를 내가 방치"하는 패턴 반복 금지

### 6단계: 상태 문서 즉시 갱신 (멈추지 않고 연속 실행)
> **GPT 판정 수신 후 사용자 보고로 멈추는 것은 금지다.**
> 반드시 아래까지 완료한 뒤 사용자 보고 1회로 마무리한다.

- PASS: TASKS.md 해당 항목 → 완료됨 이동 + HANDOFF.md/STATUS.md 갱신
- 조건부 PASS: TASKS.md 후속 항목 추가 + HANDOFF.md 미해결 기록
- FAIL: TASKS.md 항목에 FAIL 사유 기록 + 재작업 필요 표시
- 상태 문서 3종(TASKS/HANDOFF/STATUS) Edit 도구로 갱신 (dirty.flag 방지)

### 7단계: 사용자 보고 (1회 완결)
- GPT 판정 결과 1줄 요약
- 하네스 분석 1줄 (채택 N / 보류 N / 버림 N)
- 상태 문서 갱신 완료 여부
- 이후 멈추지 말고 다음 의제 발굴 또는 세션 종료 진행

### 8단계: GPT 후속 의견 1회 재확인 (루프 방지)
- GPT 마지막 응답에 추가 수정 요구가 있는지 1회만 확인
- FAIL/구조충돌 → 수정 루프 재진입
- 개선 제안 → 다음 의제로만 기록, 종료
- 후속 없음 → 종료
- **재확인은 1회만. 2회 이상 반복 금지.**

## finish_state.json 연동 (GPT 합의 2026-04-04)

`/finish` 명령에서 호출될 때 `90_공통기준/agent-control/state/finish_state.json`에 단계별 상태를 기록한다.

각 단계 완료 시 해당 필드를 true로 갱신:
- 4단계 완료 → `committed_pushed: true`
- 5단계 완료 → `gpt_shared: true`
- 6단계 완료 → `gpt_judgment: "{판정값}"`
- 7단계 완료 → `user_reported: true`
- 8단계 완료 → `followup_checked: true`, `terminal_state: "done"`

예외 발생 시 → `terminal_state: "exception"`, `exception_reason: "{사유}"`

## 주의사항
- **모든 커밋은 예외 없이 GPT에 공유한다** — 상태 문서 갱신, docs 커밋 포함. 커밋 종류에 따라 공유를 임의 생략하지 않는다
- 커밋 없이 결과만 공유 금지 — 반드시 SHA 포함
- 토론모드 규칙 준수 (Chrome MCP 단일 전송)
- 입력 전 미확인 응답 점검 필수
- **GPT 판정 수신 후 사용자 보고만 하고 멈추는 것 금지** — 상태 갱신까지 연속 실행
- **Stop guard가 finish_state.json의 terminal_state를 확인** — done/exception 아니면 종료 차단
