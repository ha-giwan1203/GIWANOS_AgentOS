# 토론모드 (debate-mode)

Claude가 GPT/Gemini와 반자동 AI 대 AI 토론을 진행한다. 2자(Claude×GPT) / 3자(Claude×GPT×Gemini) 모드 지원.

## 진입 절차

1. 토론모드 코어 규칙 읽기: `90_공통기준/토론모드/CLAUDE.md`
2. 스킬 실행 절차 읽기: `90_공통기준/토론모드/debate-mode/SKILL.md`
3. SKILL.md 절차대로 실행

## 모드 트리거

### 2자 토론 (Claude × GPT)
- "토론", "토론모드", "GPT와 토론", "debate-mode", "공동작업", "공유"

### 3자 토론 (Claude × GPT × Gemini) — 상호 감시 프로토콜
- "3자 토론", "삼자 토론", "3-way", "3-party", "Claude×GPT×Gemini"
- "Gemini도 포함", "상호 감시", "교차 검증 토론"
- **단일 모델 단독 통과 금지** — 최소 2/3 검증 통과 시만 채택
- **재라운드 최대 3회** — 초과 시 `consensus_failure.md` 기록 후 종료

## 전송/읽기 위임

- GPT 메시지 전송: `/gpt-send` 스킬 호출
- GPT 응답 읽기: `/gpt-read` 스킬 호출
- Gemini 메시지 전송 (3자 토론 필수): `/gemini-send` 스킬 호출
- Gemini 응답 읽기 (3자 토론 필수): `/gemini-read` 스킬 호출
- 수동 javascript_tool/navigate로 직접 브라우저 조작 금지
- **[NEVER]** 3자 토론 안에서 `/ask-gemini` (CLI 단발) 사용 금지 — 맥락 단절 방지

## 주의사항

### 공통
- 토론모드 CLAUDE.md를 먼저 읽지 않으면 navigate_gate에서 차단됨
- 토론방 자연어는 한국어만 사용
- 하네스 분석(채택/보류/버림) 없이 반박 전송 금지
- 독립 의견 없이 GPT/Gemini 응답 전달 금지 (debate_independent_gate 차단)

### 3자 토론 전용 (NEVER 생략)
- 매 라운드 6단계 교차 검증 필수: GPT본론 → Gemini가 GPT 1줄 검증 → Gemini본론 → GPT가 Gemini 1줄 검증 → Claude 종합 → 양측 Claude 검증
- 검증 1줄 payload에 원문 전체 동봉 (요약·발췌 금지)
- 자동 게이트 4키 검사: `gpt_verifies_gemini` / `gemini_verifies_gpt` / `gpt_verifies_claude` / `gemini_verifies_claude`
- Step 5 최종 검증은 GPT·Gemini **양측 동시** 수행 (단일 모델 단독 판정 금지)
- 커밋 시 `[3way]` 태그 + `debate_verify.sh` hook 자동 검증

### 백그라운드 탭 Throttling 대응 (세션70 실증 — NEVER 생략)
- 3자 토론 시 양측 모델 중 한쪽은 항상 백그라운드 → Chrome throttling으로 응답 DOM 누락 가능
- 매 전송/읽기 전 **대상 탭 activate 필수**: `navigate(url=대상URL, tabId=대상_tabId)` 재호출
- GPT 전송/수신 → Gemini 탭 activate → Gemini 전송/수신 순 **직렬 실행** (병렬 금지)
- 상세: `90_공통기준/토론모드/CLAUDE.md` "백그라운드 탭 Throttling 대응" 섹션 참조

## 로그 디렉터리
- 2자: `90_공통기준/토론모드/logs/debate_YYYYMMDD_HHMMSS/`
- 3자: `90_공통기준/토론모드/logs/debate_YYYYMMDD_HHMMSS_3way/`
