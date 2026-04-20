# incident_ledger 실측 집계 — 세션85 (2026-04-20)

> 원본: `.claude/incident_ledger.jsonl`
> 집계 기준: 파일 전체 (2026-04-06 ~ 2026-04-20)
> 목적: 세션시작훅 "미해결 1,004건" 주장 vs 실질 수리 대상 건수 분리

## 1. 전체 분포

| 분류 | 건수 |
|---|---|
| 총 레코드 | 1197 |
| resolved:true | 192 |
| resolved:false | 1005 |
| false_positive:true | 45 |
| false_positive:false/absent | 1152 |
| **실질 미해결** (resolved:false + fp:false) | **960** |
| 구조적 중간 미해결 (resolved:false + fp:true) | 45 |

## 2. type 분포

| type | 건수 |
|---|---|
| gate_reject | 1002 |
| warn_recorded | 61 |
| hook_block | 55 |
| ? | 50 |
| instruction_read_gate | 24 |
| doc_drift | 3 |
| gpt_verdict | 1 |
| navigate_gate | 1 |

## 3. hook 분포

| hook | 건수 |
|---|---|
| evidence_gate | 539 |
| commit_gate | 283 |
| navigate_gate | 88 |
| skill_instruction_gate | 62 |
| completion_gate | 52 |
| ? | 50 |
| harness_gate | 42 |
| instruction_not_read | 24 |
| final_check | 23 |
| date_scope_guard | 16 |
| send_gate | 7 |
| block_dangerous | 6 |
| token_threshold_check | 3 |
| gpt-read | 1 |
| gate_reject | 1 |

## 4. 실질 미해결 상위 15종 (resolved:false + fp:false)

| 건수 | type | hook | detail(선두 120자) |
|---|---|---|---|
| 246 | gate_reject | evidence_gate | map_scope.req 존재. 변경 대상/연쇄 영향/후속 작업 3줄 선언(map_scope.ok) 없이 고위험 수정 금지. |
| 159 | gate_reject | commit_gate | final_check --fast FAIL |
| 89 | gate_reject | evidence_gate | skill_read.req / identifier_ref.req 존재. SKILL.md 또는 기준정보 대조 없이 관련 도메인 수정 금지. |
| 74 | gate_reject | navigate_gate | ChatGPT 진입 차단: 토론모드 CLAUDE.md 미읽기 |
| 65 | gate_reject | evidence_gate | tasks_handoff.req 존재. TASKS/HANDOFF 갱신 없이 commit/push 금지. |
| 61 | gate_reject | skill_instruction_gate | MES access without SKILL.md read |
| 49 | warn_recorded | commit_gate | python3 의존 잔존 |
| 35 | gate_reject | commit_gate | final_check --full FAIL |
| 24 | instruction_read_gate | instruction_not_read | ? |
| 19 | hook_block | harness_gate | 하네스 분석 미수행. 누락: 채택: 보류:/버림: 독립견해 |
| 17 | gate_reject | evidence_gate | commit 차단. 이번 세션에 TASKS.md/HANDOFF.md 갱신 흔적이 없습니다. |
| 14 | gate_reject | navigate_gate | 토론모드 ChatGPT 진입 차단: CLAUDE.md 미읽기 |
| 13 | ? | ? | ? |
| 12 | hook_block | harness_gate | 하네스 분석 미수행. 누락: 독립견해 |
| 12 | warn_recorded | commit_gate | 문서 드리프트 감지 |

## 5. 구조적 중간(fp:true) 미해결 상위 10종

| 건수 | type | hook | detail(선두 120자) |
|---|---|---|---|
| 45 | gate_reject | completion_gate | 파일 변경 후 TASKS.md,HANDOFF.md 미갱신 |

## 6. 최근 24시간 hook/detail 분포

| hook | 24h 건수 |
|---|---|
| evidence_gate | 42 |
| ? | 23 |
| commit_gate | 13 |
| navigate_gate | 11 |
| instruction_not_read | 8 |
| skill_instruction_gate | 8 |
| token_threshold_check | 3 |
| harness_gate | 2 |

### 24h 주요 detail 상위 10

| 건수 | detail(선두 120자) |
|---|---|
| 31 | ? |
| 19 | skill_read.req / identifier_ref.req 존재. SKILL.md 또는 기준정보 대조 없이 관련 도메인 수정 금지. |
| 15 | commit 차단. 이번 세션에 TASKS.md/HANDOFF.md 갱신 흔적이 없습니다. |
| 11 | ChatGPT 진입 차단: 토론모드 CLAUDE.md 미읽기 |
| 9 | python3 의존 잔존 |
| 8 | map_scope.req 존재. 변경 대상/연쇄 영향/후속 작업 3줄 선언(map_scope.ok) 없이 운영 훅·settings 수정 금지. |
| 8 | MES access without SKILL.md read |
| 3 | final_check --full FAIL |
| 3 | 3회 연속 강경고 — 감축 작업 필요 |
| 1 | 하네스 분석 미수행. 누락: 채택: 보류:/버림: 독립견해 |

## 7. 일별 상위 10일

| 일자 | 건수 |
|---|---|
| 2026-04-19 | 270 |
| 2026-04-13 | 133 |
| 2026-04-14 | 132 |
| 2026-04-18 | 96 |
| 2026-04-10 | 88 |
| 2026-04-09 | 80 |
| 2026-04-20 | 79 |
| 2026-04-11 | 69 |
| 2026-04-08 | 62 |
| 2026-04-12 | 53 |

## 8. 세션85 해석 (Claude)

- 세션시작훅 "미해결 1,004건"은 `resolved:false` 단일 필드 기준 — 대부분은 gate의 정상 차단 기록(operational log)이지 버그가 아니다.
- `false_positive:true`로 명시된 것은 45건에 그친다. 이는 세션80·83에서 retrospective 마킹한 과거 debate_verify 오탐 건이 주류.
- **실질 조사 가치가 있는 건수**: 960건. 그중 상위 5종이 전체의 약 65% 이상을 차지한다(후술).
- 상위 5종은 모두 **정책성 차단(policy gate)** 으로 "코드 버그"가 아닌 "사용자/AI 행위 규정 위반의 누적 기록". 수리 대상이 아니라 **운영 규칙 준수 여부의 지표**다.
  1. evidence_gate `map_scope.req` (246): /map-scope 선언 없이 설정 변경 시도
  2. commit_gate `final_check --fast FAIL` (159): 커밋 직전 final_check FAIL (대부분 TASKS/HANDOFF 미갱신 또는 evidence 계열)
  3. evidence_gate `skill_read.req` (89): SKILL.md 미읽은 상태에서 스킬 실행 시도
  4. navigate_gate `CLAUDE.md 미읽기` (74): 토론모드 진입 직전 차단
  5. evidence_gate `tasks_handoff.req` (65): TASKS/HANDOFF 미갱신 상태 commit/push

### 권고

- 1,196건 전체에 `/auto-fix` 스킬 일괄 적용은 **부적합**. 단일 코드 결함이 아닌 정책 게이트 로그이기 때문.
- 개선 방향(차기 세션 이월):
  - (a) gate_reject 중 동일 fingerprint 반복(`map_scope.req` 246건 등)은 evidence_gate의 **self-throttle 확장**이 근본 해결. 세션83 A안(GRACE 120s + tail -100) 이후 추가 효과 측정 필요
  - (b) `final_check --fast FAIL` 159건은 커밋 직전 사용자/AI가 TASKS/HANDOFF 갱신을 놓친 재발 패턴 — `/finish` 스킬 사용률 제고·completion_gate 소프트 블록 정책 재검토
  - (c) `resolved:true` 대량 retrospective 마킹 루틴(세션80 패턴) 재실행은 위험 — 근본 해결 아닌 지표 마사지. 지양.
- **Step 2.5 판정**: `/auto-fix` 호출 보류. ledger는 정책 준수 지표로 기능하고 있어 일괄 수리 대상이 아니다.
