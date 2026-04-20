# C 의제 Round 1 — gpt-read/gpt-send thinking 확장추론 대응 (세션83 API 예외)

일시: 2026-04-20 14:47~14:50 KST
- 사용 모델: Gemini 3.1-pro-preview + GPT-5.2 (2025-12-11)

## 배경
세션82 실증: gpt-5-4-thinking 모델 응답 중 stop-button 지속 유지되며 300초 타임아웃 → Claude stop 오클릭 → 사용자 수동 중재

## 판정 매트릭스

| 문항 | GPT-5.2 | Gemini 3.1-pro-preview | Claude 종합 |
|------|---------|----------------------|-------------|
| Q1 slug 탐지 | 보류 (allowlist 권장) | 채택 `includes('thinking')` | **`slug.toLowerCase().includes('thinking')\|\|includes('reasoning')` — 미래 변형 + reasoning 대응, allowlist는 단순화 이유로 미채택** |
| Q2 polling | 채택(수정) — 300초 이후만 30초 | 채택 | **isExtended=true 시 3/5/8/15초 반복, 300초 이후 30초, 최대 600초** |
| Q3 종료 판정 | 채택 (B+변형) — 네트워크 idle + DOM 안정 | 채택 (A) — stop-button + MutationObserver | **DOM 기반 (A) — 블록 안정 3회 연속 동일. 네트워크 hook은 스크립트 환경 취약 (Gemini 지적 타당)** |

## 구현 (3파일)

1. `.claude/commands/gpt-read.md` 2-a 확장:
   - `data-message-model-slug` lowercase + `includes('thinking'|'reasoning')` 판정
   - `maxTimeout: isExtended ? 600 : 300`
   - 종료 조건 OR: (stop-button=false + 안정성 기존) OR (블록 안정 3회 연속 동일, stop-button 잔존 무관)
   - 변경이력 세션83 추가

2. `.claude/commands/gpt-send.md` 4단계 보완:
   - isExtended 감지 JS 동기화
   - polling 단계 2/3/5/8초 반복, 후기 15/30초 (일반 300초 / 확장 600초)
   - 명시적 "stop-button 단독 판정 금지"

3. `.claude/hooks/smoke_test.sh` 섹션 49 신설 (5건):
   - 49-1 gpt-read thinking/reasoning 감지 grep
   - 49-2 maxTimeout 600:300 삼항 분기
   - 49-3 "블록 안정 3회 연속 동일" 문구 확인
   - 49-4 gpt-send 동기화 확인
   - 49-5 "stop-button 단독 판정 금지" 명시

## 3자 비교에서 독립 판정

- GPT-5.2의 **(B) 네트워크 idle**: DOM-agnostic 장점 있으나 Chrome MCP에서 XHR/fetch intercept 불안정 (세션69 실증) → **미채택**
- Gemini의 **MutationObserver**: 이미 존재하는 "2회 연속 동일 측정" 로직과 중복 → **3회 연속 동일 확장**으로 단순화
- 양측 공통 지적 **slug allowlist**: 현재 시점 `thinking`/`reasoning` 2종만 반영, 향후 추가 slug는 별건으로 확장
