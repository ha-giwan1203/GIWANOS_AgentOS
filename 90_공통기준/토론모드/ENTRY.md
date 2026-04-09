# 토론모드 Active Laws (ENTRY.md)

> 앱 자체지침: `90_공통기준/토론모드/APP_INSTRUCTIONS.md`
> 이 파일은 코어 금지/강제 규칙, `APP_INSTRUCTIONS.md`는 앱 운영 기준이다.

> 이 파일이 Primary. CLAUDE.md는 Reference(상세 배경용).
> 위반 = 버그. hooks가 강제한다.

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

## 필수 순서 (SHOULD → NEVER 승격 대상)

1. 기존 탭 확인 → 있으면 switch
2. main 영역 JS로 대화 URL 추출 → navigate
3. **[SEND GATE] 전송 직전 미확인 응답 점검** (NEVER 5 강제)
   - 마지막 assistant 블록 텍스트 100자 읽기
   - 이전에 읽은 내용과 다르면 → 새 응답 먼저 전체 읽기 → 하네스 재계산 → 그 다음 전송
   - 같으면 → 예정대로 전송 진행
4. 기본 전송 경로는 `.claude/scripts/cdp/cdp_chat_send.py --require-korean --mark-send-gate`
   - Step 3에서 읽은 최신 답변 100자는 `--expect-last-snippet` 또는 `--expect-last-snippet-file`로 함께 넘긴다.
   - helper가 현재 화면의 최신 답변 100자와 다르다고 판단하면 전송하지 않고 차단해야 한다.
5. helper를 쓸 수 없을 때만 `#prompt-textarea` + `execCommand('insertText')` + `[data-testid="send-button"], #composer-submit-button` JS 클릭
6. stop-button polling 적응형 (3/5/8초) + 매 주기 사용자 중단 확인

## 상세 참조

selector 목록, fallback 체인, 오류 대응, 로그 형식 → `CLAUDE.md` 참조
