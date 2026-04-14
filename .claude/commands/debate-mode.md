# 토론모드 (debate-mode)

Claude가 GPT 프로젝트방에서 반자동 AI 대 AI 토론을 진행한다.

## 진입 절차

1. 토론모드 코어 규칙 읽기: `90_공통기준/토론모드/CLAUDE.md`
2. 스킬 실행 절차 읽기: `90_공통기준/토론모드/debate-mode/SKILL.md`
3. SKILL.md 절차대로 실행

## 전송/읽기 위임

- GPT 메시지 전송: `/gpt-send` 스킬 호출
- GPT 응답 읽기: `/gpt-read` 스킬 호출
- 수동 javascript_tool/navigate로 직접 브라우저 조작 금지

## 주의사항
- 토론모드 CLAUDE.md를 먼저 읽지 않으면 navigate_gate에서 차단됨
- 토론방 자연어는 한국어만 사용
- 하네스 분석(채택/보류/버림) 없이 반박 전송 금지
- 독립 의견 없이 GPT 응답 전달 금지 (debate_independent_gate 차단)
