# Hook 4지표 집계

- 생성시각: 2026-04-11T14:39:44+09:00
- hook_log: 3865건 / incident_ledger: 319건

## 합계

| 지표 | 건수 | 비율 |
|------|------|------|
| 승인 요청 (hook 발화) | 1791 | - |
| deny (raw) | 319 | 17.81% |
| deny (effective, 오탐 제외) | 274 | 15.30% |
| 오탐 (false_positive) | 45 | 14.11% |
| 우회 감지 | 0 | 0.00% |

## hook별 상세

| hook | 발화 | deny | 오탐 | 우회 |
|------|------|------|------|------|
| evidence_gate | 2 | 202 | 0 | 0 |
| completion_gate | 0 | 52 | 45 | 0 |
| commit_gate | 111 | 46 | 0 | 0 |
| date_scope_guard | 665 | 7 | 0 | 0 |
| block_dangerous | 665 | 6 | 0 | 0 |
| send_gate | 8 | 6 | 0 | 0 |
| protect_files | 176 | 0 | 0 | 0 |
| risk_profile_prompt | 2 | 0 | 0 | 0 |
| unknown | 160 | 0 | 0 | 0 |
| write_marker | 2 | 0 | 0 | 0 |

## 판정 기준

- deny_rate_raw = deny 전체 / 승인요청 (가드레일 강도)
- deny_rate_effective = (deny - 오탐) / 승인요청 (실제 위반 비율)
- false_positive_rate = 오탐 / deny (높으면 잘못 막는 비율 높음)
- bypass_rate = 우회 / 승인요청 (0이어야 정상)
- 오탐 태깅: incident_ledger에서 false_positive=true 또는 classification=fp/오탐으로 표기
