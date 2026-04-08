# 토론모드 Active Laws (ENTRY.md)

> 이 파일이 Primary. CLAUDE.md는 Reference(상세 배경용).
> 위반 = 버그. hooks가 강제한다.

## NEVER (위반 시 hooks 차단)

1. 클립보드 붙여넣기 입력 금지 — `execCommand('insertText')` only
2. ref 클릭 전송 금지 — `[data-testid="send-button"]` JS 클릭 only
3. find()/form_input 입력 금지
4. 새 대화 개설 금지 — `.claude/state/debate_chat_url`에 URL이 있으면 반드시 해당 URL로 진입. 새 대화 허용 조건: (a) debate_chat_url 파일 없음 AND (b) 프로젝트 main 영역에 기존 대화 0건
5. SEND GATE: 전송 직전 assistant 최신 텍스트 재읽기 → 변경 시 재계산 필수 — 생략 금지

## NEVER (분석)

6. 하네스 분석 없이 반박 전송 금지 — 채택/보류/버림 필수
7. 반박문에 `채택:` `보류:` `버림:` 누락 금지

## 필수 순서 (SHOULD → NEVER 승격 대상)

1. 기존 탭 확인 → 있으면 switch
2. main 영역 JS로 대화 URL 추출 → navigate
3. **[SEND GATE] 전송 직전 미확인 응답 점검** (NEVER 5 강제)
   - 마지막 assistant 블록 텍스트 100자 읽기
   - 이전에 읽은 내용과 다르면 → 새 응답 먼저 전체 읽기 → 하네스 재계산 → 그 다음 전송
   - 같으면 → 예정대로 전송 진행
4. `#prompt-textarea` + `execCommand('insertText')`
5. `[data-testid="send-button"]` JS 클릭
6. stop-button polling 적응형 (3/5/8초) + 매 주기 사용자 중단 확인

## 상세 참조

selector 목록, fallback 체인, 오류 대응, 로그 형식 → `CLAUDE.md` 참조
