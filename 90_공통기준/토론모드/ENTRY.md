# 토론모드 진입 핵심 규칙 (ENTRY.md)

> domain_guard가 강제하는 최소 읽기 대상. 이 파일 읽기 → CLAUDE.md 읽기 → 실행.

## 필수 순서
1. 기존 ChatGPT 탭 확인 (tabs_context_mcp) → 있으면 switch, 없으면 프로젝트 URL navigate
2. main 영역에서 JS로 대화 URL 추출 → navigate (클릭 금지)
3. 입력: `#prompt-textarea` + `execCommand('insertText')` (클립보드/DataTransfer 금지)
4. 전송: `[data-testid="send-button"]` JS 클릭 (ref 클릭 금지)
5. 응답 대기: stop-button polling 적응형 (5/10/15초)
6. 입력 전 미확인 응답 점검 필수

## 필수 분석
- GPT 응답 → 주장 분해 → 라벨링(실증/일반론/환경미스매치/과잉) → 채택/보류/버림
- 반박문 첫 문단에 `채택:` `보류:` `버림:` 포함

## 금지
- 프로젝트방 외 새 대화 개설
- find() → form_input 입력
- 클립보드 붙여넣기 입력
- ref 클릭으로 전송
- 중간 승인 요청 (비가역 제외)
