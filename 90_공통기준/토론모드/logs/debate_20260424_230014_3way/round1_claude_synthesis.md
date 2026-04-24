# Q4 Round 1 — Claude 종합 설계안

## 진행 결과 요약
- Round 1 GPT: A안 (최소보강) — navigate_page/new_page 매처 확장, select_page 제외
- Round 1 Gemini: A안 (최소보강) — 동일 결론
- 교차 검증: 6-2 Gemini→GPT=동의 / 6-4 GPT→Gemini=동의 (pre-6-5 pass 2/2)

## 최종 설계안 (Q4)

### 채택
**A안 — 최소보강** (양측 동일 결론, 이견 없음)

### 구체 실행 계획

**Step 1 — settings.json PreToolUse matcher 확장**
- 기존: `mcp__Claude_in_Chrome__navigate`
- 추가: `mcp__chrome-devtools-mcp__navigate_page`, `mcp__chrome-devtools-mcp__new_page`
- 제외 (URL 진입 아님): `select_page`, `evaluate_script`, `take_snapshot`, `click`, `fill`

**Step 2 — navigate_gate.sh 파싱 로직 확장**
- 기존 URL 추출: `tool_input.url` / `url`
- `new_page` 도구: `tool_input.url` (navigate URL 필드)
- `navigate_page` 도구: `tool_input.url` 추출 AND `tool_input.type == "url"`일 때만 검사 (reload/back/forward 제외)

**Step 3 — 회귀 테스트 스크립트**
- 네거티브: marker 없음 + navigate_page chatgpt.com → 차단
- 포지티브: marker 생성 후 동일 진입 → 통과
- 비대상: select_page(bringToFront=true) → 차단 안 됨
- 회귀: 기존 Claude_in_Chrome__navigate 차단 로직 유지

**Step 4 — 문서 갱신**
- `.claude/hooks/README.md` hook 개수 갱신
- `STATUS.md` hook 개수 갱신
- `AGENTS_GUIDE.md` 자동 섹션 갱신

### 효과성 평가 (재라운드 트리거)
- 적용 후 7일간:
  - navigate_gate send_block 0~2건: 정상 (GPT 제시)
  - 부당 차단 오탐 3건 이상 발생: 재상정 (Gemini 제시)
- 두 지표 중 하나라도 임계 충족 시 Round 2 재검토

## claude_delta 선언
- `claude_delta = "none"` — 양측 A안 단순 축약, 신규 정책/예외 추가 없음
- `issue_class = "B"` — hook matcher 변경 + 실행 흐름 영향
- `skip_65 = false` (B분류 필수 + round_count 1이지만 B분류 강제)

## cross_verification 요약 (pre-6-5)

```json
{
  "gemini_verifies_gpt": {"verdict": "동의", "reason": "URL 신규 로드 도구(navigate_page, new_page)만 통제에 추가, select_page 제외는 오탐 최소화의 실용적 접근"},
  "gpt_verifies_gemini": {"verdict": "동의", "reason": "GPT A안 최소보강 결론과 동일, 보안 커버리지와 오탐 억제 동시 맞춤"},
  "gpt_verifies_claude": "대기",
  "gemini_verifies_claude": "대기",
  "pass_ratio_pre_65": "2/2",
  "round_count": 1,
  "max_rounds": 3,
  "skip_65": false,
  "claude_delta": "none",
  "issue_class": "B"
}
```
