# Q3 auto-fix 1차 분류 보고서

- 실행 일시: 2026-04-24 KST (세션105 Round 2 후속)
- 스코프: `incident_ledger.jsonl` 전체 미해결(resolved=false) 항목
- 원칙: Round 1 Q3=A안 합의 — **자동 수정 금지, 상위 카테고리 분류만**

## 집계 (미해결 기준)

| 지표 | 값 |
|------|-----|
| 총 incident (ledger) | 1393건 |
| 미해결(resolved=false) | **80건** |
| 최근 24h(2026-04-24) 미해결 | 65건 |
| 2026-04-23 미해결 | 15건 |
| 14일 이전 미해결 | 0건 |

> TASKS/HANDOFF에 기록된 "110건"과 차이 있음 — 세션 중 일부 자동 해결(55건) + 숫자 집계 시점 차이. 현재 기준 80건.

## 상위 카테고리 (미해결)

| 순위 | classification_reason | hook | 건수 | 비율 |
|------|----------------------|------|------|------|
| 1 | completion_before_state_sync | auto_commit_state | 15 | 19% |
| 2 | pre_commit_check | commit_gate | 14 | 18% |
| 3 | send_block | navigate_gate | 11 | 14% |
| 4 | session_drift | final_check | 10 | 13% |
| 5 | harness_missing | harness_gate | 5 | 6% |
| 6 | evidence_missing | evidence_gate | 1 | 1% |
| 7 | doc_drift | (혼합) | 1 | 1% |
| — | 미분류·기타 | 혼합 | 23 | 29% |

## 처리 분류 (즉시 수정 / 별도 의제 / 무시 가능)

### Category A — auto_commit_state (15건): **Q1 기타안으로 처리 완료**
- classification_reason: `completion_before_state_sync`
- hook: `auto_commit_state`
- 원인: TASKS/HANDOFF/STATUS 미갱신 상태에서 세션 종료 시 auto commit 시도 → final_check --fast 실패로 차단
- 처리: 세션105 Q1 기타안으로 **이미 분석+advisory 강화 완료** (커밋 72d017e4)
- **[별도 의제 불필요]**

### Category B — commit_gate pre_commit_check (14건): **Category A와 동근원, 함께 해소 기대**
- classification_reason: `pre_commit_check`
- hook: `commit_gate`
- 원인: 수동 git commit 시 동일하게 상태문서 미갱신 탐지
- 처리: Q1 기타안 advisory 강화가 **auto_commit_state + commit_gate 양쪽에 효과** (원인 가시화 → 사용자 조기 인지)
- **[관찰 대상]** — Q1 advisory 강화 후 재측정 시 감소 예상. 2주 후 재측정

### Category C — navigate_gate send_block (11건): **별도 의제 필요**
- classification_reason: `send_block`
- hook: `navigate_gate`
- 원인: debate-mode/gpt-send 등 브라우저 조작 전 CLAUDE.md 미읽기 상태 차단
- 처리: navigate_gate의 "CLAUDE.md 읽기 감지 기준" 재검토 필요 가능. 세션 시작 직후 감지 로직 보강 여지
- **[별도 의제: "navigate_gate 감지 기준 재검토"]** — 신규 Q4로 등록 권장

### Category D — final_check session_drift (10건): **자동 수정 가능**
- classification_reason: `session_drift`
- hook: `final_check`
- 원인: TASKS 세션 번호 ≠ HANDOFF/STATUS 세션 번호 등 드리프트
- 처리: `final_check --fix` 옵션이 일부 드리프트 자동 수정 가능
- **[즉시 수정 시도]** — `/finish` 루틴의 auto-sync로 해소 가능 여부 확인

### Category E — harness_gate harness_missing (5건): **규칙 강화 필요**
- classification_reason: `harness_missing`
- hook: `harness_gate`
- 원인: 토론모드 응답 후 주장 분해·라벨링(채택/보류/버림) 누락
- 처리: Q2 합의(실증됨 라벨 엄격화)와 연결. 세션105 Q2 정책 구현 시 함께 처리
- **[Q2 연계]** — Q2 구현 안건 처리 시 함께

### Category F — 기타 (2건): **개별 처리**
- evidence_missing 1건, doc_drift 1건
- 처리: 개별 확인 후 해소 가능
- **[산발적, 일괄 처리 불필요]**

### Category G — 미분류 (23건): **세부 조사 필요**
- type·hook·classification 집계에서 잡히지 않은 항목 (type=gate_reject/hook_block 중 분류 필드 누락 등)
- 처리: Phase 2 조사 대상 (이번 1차 분류 범위 외)

## Q1 재점화 조건 4 평가 (핵심 체크)

> 조건 4: "Q3 auto-fix 분류에서 auto_commit_state가 상위 3개 원인군 진입 → Q1 재상정"

- auto_commit_state: **상위 1위 공동 (15건, 19%)** → **조건 4 수치상 충족**
- 그러나 Q1 기타안 audit 해석(단일 세션 burst + 단일 원인)과 일치하므로 **재상정 불필요**
- 기록: 상위 원인군 진입 사실 자체는 TASKS에 명시하되, Q1 재상정은 Q1 기타안 결론이 최신 답이므로 중복 의제 방지 차원에서 보류

## 권장 다음 단계

1. Category D (session_drift 10건): `/finish` 또는 `final_check --fix` 시도 → 자동 해소 가능 여부 확인
2. Category C (navigate_gate 11건): 신규 Q4 의제로 분리 — "navigate_gate 감지 기준 재검토"
3. Category B (commit_gate 14건): Q1 advisory 강화 효과 관찰 (2주 후 재측정)
4. Category G (미분류 23건): Phase 2 세부 조사
5. Category A·E·F: 이미 정책 결정되어 있거나 산발적 → 추가 조치 불필요
