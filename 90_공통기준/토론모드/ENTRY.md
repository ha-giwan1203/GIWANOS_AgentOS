# 토론모드 Active Laws (ENTRY.md)

> 앱 자체지침: `90_공통기준/토론모드/APP_INSTRUCTIONS.md`
> 이 파일은 코어 금지/강제 규칙, `APP_INSTRUCTIONS.md`는 앱 운영 기준이다.

> 이 파일이 Primary. CLAUDE.md는 Reference(상세 배경용).
> 위반 = 버그. hooks가 강제한다.

## 스킬 진입 (MUST)

- 토론/공동작업/공유 관련 요청 → **`/debate-mode` 스킬 호출 필수**
- 수동 navigate, gpt-send 스킬로 우회 진입 금지
- UserPromptSubmit 훅이 토론 키워드 감지 시 systemMessage로 안내
- navigate_gate 훅이 CLAUDE.md 미읽기 시 ChatGPT 진입 차단

## NEVER (위반 시 hooks 차단)

1. 직접 DOM 예비 경로에서 클립보드 붙여넣기 입력 금지 — `execCommand('insertText')` only
2. 직접 DOM 예비 경로에서 ref 클릭 전송 금지 — `[data-testid="send-button"], #composer-submit-button` JS 클릭 only
3. find()/form_input 입력 금지
4. 새 대화 개설 금지 — `.claude/state/debate_chat_url`에 URL이 있으면 반드시 해당 URL로 진입. 새 대화 허용 조건: (a) debate_chat_url 파일 없음 AND (b) 프로젝트 main 영역에 기존 대화 0건
5. SEND GATE: 전송 직전 assistant 최신 텍스트 재읽기 → 변경 시 재계산 필수 — 생략 금지
6. 토론방 자연어 영어 사용 금지 — 질문/반박/검증 요청/완료 보고는 한국어만 사용. 예외: code block, selector/data-testid, 파일 경로, commit SHA 같은 literal

## NEVER (분석)

7. 하네스 분석 없이 반박 전송 금지 — 채택/보류/버림 필수
8. 반박문에 `채택:` `보류:` `버림:` 누락 금지
9. **Claude 독립 검토 생략 금지** — GPT 전송 전 반드시 Claude 자체 분석 먼저 수행:
   - 문제 원인 우선순위 (내 판단)
   - 즉시 개선 가능한 것 vs 구조적 한계
   - GPT가 놓칠 가능성 있는 포인트 예상
10. **최종 통합 검토 생략 금지** — 하네스 분석 후 반드시 Claude 최종 입장 정리:
    - GPT 일치 부분 / 이견 부분(내 근거 명시) / 두 분석 모두 놓친 맹점
    - 사용자 보고: `채택 N건 / 보류 N건 / 버림 N건` + 실행 우선순위 3가지 + GPT와 쟁점 명시

## 브라우저 조작 금지 (NEVER)

11. **debate-mode 안에서 Chrome MCP 도구 직접 호출 금지** — tabs_context_mcp, navigate, javascript_tool, get_page_text, find, computer 등 전부 금지. 브라우저 조작은 gpt-send/gpt-read 스킬이 내부에서 처리한다. debate-mode는 토론 로직(독립 점검, 하네스 분석, 반박 생성, 로그 기록)만 담당한다.

## gpt-send/gpt-read 내부 순서 (참고 — debate-mode가 직접 실행하지 않음)

1. 탭 확인 → 프로젝트 URL navigate → 최상단 채팅방 재탐지 (gpt-send 1-A/1-B)
2. SEND GATE: 미확인 응답 점검 (gpt-send Step 2)
3. insertText + send button 클릭 (gpt-send Step 3)
4. 적응형 polling 대기 (gpt-send Step 4)
5. 응답 읽기 (gpt-send Step 5 / gpt-read Step 3)

## 상세 참조

selector 목록, fallback 체인, 오류 대응, 로그 형식 → `CLAUDE.md` 참조
