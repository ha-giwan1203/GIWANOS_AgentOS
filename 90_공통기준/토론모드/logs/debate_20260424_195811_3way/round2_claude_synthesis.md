# Round 2 — Claude 종합 설계안

## 진행 결과 요약
- Round 1: GPT=C / Gemini=B 불일치
- Round 2 GPT: 기타안 (B 실측 선행 채택 + C 임계값 구현 보류)
- Round 2 Gemini: 기타안 동조 (TASKS 조건 1건만 tightening)
- 교차 검증: 6-2 Gemini→GPT=동의 / 6-4 GPT→Gemini=동의 (6-2/6-4 pass 2/2)

## 최종 설계안 (Q1)

### 채택
- **기타안** — B안 "실측 선행" + C안 "임계값 구현 폐기" 병합

### 구체 실행 계획

**Step 1 — 실측 audit (1회, 필수)**
- `.claude/incident_ledger.jsonl`에서 auto_commit_state 태그 grep
- 최근 14일 기준 건수·최초/최종 시각·간격·classification_reason 추출
- 결과 보고서: `90_공통기준/토론모드/logs/debate_20260424_195811_3way/audit_auto_commit_state.md`

**Step 2 — advisory 경고 가시성 강화**
- 기존 auto_commit_state 차단 기능 유지 (변경 없음)
- hook_incident 로그 문구 강화 (파일·커밋 SHA·원인 분류 명시)
- 하드페일/자동 격상 로직 **구현 제외**

**Step 3 — 재점화 트리거 등록 (임계값 아닌 의제 재개 조건)**

Gemini tightening 반영:
1. auto_commit_state 태그 incident 최근 7일 3건 이상 AND 그중 2건 이상 final_check --fast 실패 → 재상정
2. auto_commit_state 차단 후 **상태 불일치로 인한 롤백 발생** 사례 1건 이상 → 재상정 (Gemini 요구 반영: 단순 TASKS 미동기화 ≠ 자동 트리거)
3. push 실패가 hook 설계 문제로 2회 이상 반복 → **긴급 whitelist/로직 수정 근거** (격상 아님, Gemini 요구 반영)
4. Q3 `/auto-fix` 분류에서 auto_commit_state가 상위 3개 원인군 진입 → 재상정

### 완료 기준
- TASKS.md에 "Q1 = 기타안, 임계값 구현 보류, 실측 audit 후 재점화 조건 4건 등록" 기록
- `audit_auto_commit_state.md` 결과 Git 커밋
- advisory 경고 문구 강화 Git 커밋
- auto_commit_state.sh 실행 흐름 변경 없음 확인
- hook count 변화 없음 확인

### 검증 방법
- incident_ledger grep 결과 원문 5줄 이내 샘플 첨부
- classification_reason별 카운트 기록
- Q3 auto-fix 결과와 비교 → auto_commit_state 상위 원인군 여부 확인

## claude_delta 선언
- `claude_delta = "partial"` — GPT 기타안 + Gemini 2건 조건 tightening 통합
- `issue_class = "B"` — hook 설계·재점화 조건 신설 (실행 흐름 변경은 없으나 정책 변경)
- `skip_65 = false` (Round 2 필수 + B분류)

## cross_verification 최종

```json
{
  "gemini_verifies_gpt": {"verdict": "동의", "reason": "신설된 훅의 표본 부족 문제 지적 + 실측 선행 + 임계값 구현 보류가 프로젝트 보수적 판단 원칙에 부합"},
  "gpt_verifies_gemini": {"verdict": "동의", "reason": "Gemini가 B안의 핵심 약점인 표본 부족·80% 커버 과잉을 인정하고 기타안으로 정리했기 때문에 Round 2 GPT 판단과 정합"},
  "gpt_verifies_claude": {"verdict": "동의", "reason": "양측 합의인 \"실측 audit은 수행하되 자동 격상 로직은 구현하지 않는다\"는 범위를 유지하면서, Gemini 보정 조건까지 반영해 재상정 트리거와 긴급 수정 트리거를 분리했으므로 정합"},
  "gemini_verifies_claude": {"verdict": "동의", "reason": "양측이 합의한 '실측 선행 및 임계값 구현 보류' 기조와 상태 불일치 롤백 등 엄격해진 재상정 4조건이 누락 없이 정확히 통합되었음"},
  "pass_ratio_numeric": 1.0,
  "pass_count": "4/4",
  "round_count": 2,
  "max_rounds": 3,
  "skip_65": false,
  "claude_delta": "partial",
  "issue_class": "B",
  "verdict": "합의 성립 — Q1 = 기타안 채택"
}
```

## 판정
Round 2 **합의 성립**. Q1 최종안 = 기타안 (B 실측 선행 + C 임계값 구현 폐기 + 재점화 4조건). 즉시 착수 가능.
