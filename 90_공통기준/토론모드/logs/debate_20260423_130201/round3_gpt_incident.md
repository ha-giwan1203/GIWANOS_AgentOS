# Round 3 — GPT 응답 (incident 의제, 같은 토론 채널)

판정: **조건부 통과**

## A 분류 동의
동의. incident_repair.py auto-resolve 규칙 확대는 사후 ledger 정리층 변경. commit_gate/evidence_gate/final_check 실시간 판정 흐름 변경 아님. rule 6 선례 동일.

## rule 7 (harness_missing) 우회 충분성
대체로 충분. 72h만으로 닫지 않고 무재발 0건 부착. 다만 detail exact match 취약 — `detail.strip()` 정규화 또는 classification_reason + hook + normalized_detail 권장 (선택).

## rule 8 (meta_drift)
통과. 4개 중 가장 명확. 그대로 가도 됨.

## rule 9 (doc_drift) — 보강 필요
**age-only 위험**. 현재 detail은 generic "문서 드리프트 감지"이고 실제 drift subtype은 `warn_keywords` 쪽. age-only면 살아있는 drift도 "오래됐으니 정리"로 닫힐 여지. 둘 중 하나 추가 필수:
1. 현재 final_check --fast 결과에 drift WARN 없음
2. incident의 warn_keywords/subtype과 같은 drift가 현재 재현 안 됨

## rule 10 (evidence_missing) — 보강 필요
"detail 빈 문자열이거나 ts<now-72h" 조건 너무 느슨. 보정:
1. **72h 항상 필수** (empty 예외 제거)
2. 무재발 키: **fingerprint 우선 / 없으면 hook + normalized_detail fallback**

## 누락 규칙 후보
지금 추가 X. legacy_unclassified는 backfill_classification 선행, send_block은 .ok mtime 이미 있음, unknown은 분류 정상화 먼저.

## 종합
**조건부 통과**. 보정 2개:
1. rule 9 age-only 금지 → 현재 drift 미재현 조건 추가
2. rule 10 detail empty 예외 제거. 72h 항상 필수, fingerprint 우선/normalized_detail fallback

다음 행동: rule 8 그대로, rule 7 거의 그대로, rule 9·10만 보강 후 구현.
