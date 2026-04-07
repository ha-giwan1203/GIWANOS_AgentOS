# Hook 4지표 집계

- 생성시각: 2026-04-08T07:37:37+09:00
- hook_log: 3663건 / incident_ledger: 53건

## 합계

| 지표 | 건수 | 비율 |
|------|------|------|
| 승인 요청 (hook 발화) | 1686 | - |
| deny (차단) | 53 | 3.14% |
| 오탐 (false_positive) | 0 | 0.00% |
| 우회 감지 | 0 | 0.00% |

## hook별 상세

| hook | 발화 | deny | 오탐 | 우회 |
|------|------|------|------|------|
| completion_gate | 0 | 23 | 0 | 0 |
| commit_gate | 144 | 18 | 0 | 0 |
| block_dangerous | 802 | 6 | 0 | 0 |
| date_scope_guard | 448 | 4 | 0 | 0 |
| evidence_gate | 4 | 1 | 0 | 0 |
| send_gate | 2 | 1 | 0 | 0 |
| evidence_mark_read | 2 | 0 | 0 | 0 |
| evidence_stop_guard | 2 | 0 | 0 | 0 |
| gpt_followup_stop | 4 | 0 | 0 | 0 |
| notify_slack | 3 | 0 | 0 | 0 |
| protect_files | 262 | 0 | 0 | 0 |
| risk_profile_prompt | 3 | 0 | 0 | 0 |
| stop_guard | 5 | 0 | 0 | 0 |
| write_marker | 5 | 0 | 0 | 0 |

## 판정 기준

- deny_rate = deny / 승인요청 (높으면 규칙이 너무 엄격)
- false_positive_rate = 오탐 / deny (높으면 잘못 막는 비율 높음)
- bypass_rate = 우회 / 승인요청 (0이어야 정상)
- 오탐 태깅: incident_ledger에서 false_positive=true 또는 classification=fp/오탐으로 표기
