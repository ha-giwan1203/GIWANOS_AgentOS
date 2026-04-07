# Hook 4지표 집계

- 생성시각: 2026-04-08T06:30:09+09:00
- hook_log: 3097건 / incident_ledger: 50건

## 합계

| 지표 | 건수 | 비율 |
|------|------|------|
| 승인 요청 (hook 발화) | 1485 | - |
| deny (차단) | 50 | 3.37% |
| 오탐 (resolved) | 0 | 0.00% |
| 우회 감지 | 0 | 0.00% |

## hook별 상세

| hook | 발화 | deny | 오탐 | 우회 |
|------|------|------|------|------|
| completion_gate | 2 | 22 | 0 | 0 |
| commit_gate | 89 | 16 | 0 | 0 |
| block_dangerous | 728 | 6 | 0 | 0 |
| date_scope_guard | 372 | 4 | 0 | 0 |
| evidence_gate | 0 | 1 | 0 | 0 |
| send_gate | 1 | 1 | 0 | 0 |
| evidence_stop_guard | 2 | 0 | 0 | 0 |
| gpt_followup_post | 7 | 0 | 0 | 0 |
| gpt_followup_stop | 4 | 0 | 0 | 0 |
| notify_slack | 3 | 0 | 0 | 0 |
| protect_files | 224 | 0 | 0 | 0 |
| risk_profile_prompt | 3 | 0 | 0 | 0 |
| unknown | 45 | 0 | 0 | 0 |
| write_marker | 5 | 0 | 0 | 0 |

## 판정 기준

- deny_rate = deny / 승인요청 (높으면 규칙이 너무 엄격)
- false_positive_rate = 오탐 / deny (높으면 잘못 막는 비율 높음)
- bypass_rate = 우회 / 승인요청 (0이어야 정상)
- 오탐 태깅: incident_ledger에서 resolved=true로 수동 표기
