# 토론모드 Active Laws (ENTRY.md)

> 이 파일이 Primary. CLAUDE.md는 Reference(상세 배경용).
> 위반 = 버그. hooks가 강제한다.

## NEVER (위반 시 hooks 차단)

1. 클립보드 붙여넣기 입력 금지 — `execCommand('insertText')` only
2. ref 클릭 전송 금지 — `[data-testid="send-button"]` JS 클릭 only
3. find()/form_input 입력 금지
4. 프로젝트방 외 새 대화 개설 금지
5. 입력 전 미확인 응답 점검 생략 금지

## NEVER (분석)

6. 하네스 분석 없이 반박 전송 금지 — 채택/보류/버림 필수
7. 반박문에 `채택:` `보류:` `버림:` 누락 금지

## 필수 순서 (SHOULD → NEVER 승격 대상)

1. 기존 탭 확인 → 있으면 switch
2. main 영역 JS로 대화 URL 추출 → navigate
3. `#prompt-textarea` + `execCommand('insertText')`
4. `[data-testid="send-button"]` JS 클릭
5. stop-button polling 적응형 (5/10/15초)
6. 입력 전 미확인 응답 점검

## 상세 참조

selector 목록, fallback 체인, 오류 대응, 로그 형식 → `CLAUDE.md` 참조
