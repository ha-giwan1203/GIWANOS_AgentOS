# Hook 4지표 집계

- 생성시각: 2026-04-12T18:34:34+09:00
- hook_log: 2505건 / incident_ledger: 370건

## 합계

| 지표 | 건수 | 비율 |
|------|------|------|
| 승인 요청 (hook 발화) | 1114 | - |
| deny (raw) | 370 | 33.21% |
| deny (effective, 오탐 제외) | 325 | 29.17% |
| 오탐 (false_positive) | 45 | 12.16% |
| 우회 감지 | 0 | 0.00% |

## hook별 상세

| hook | 발화 | deny | 오탐 | 우회 |
|------|------|------|------|------|
| evidence_gate | 1 | 237 | 0 | 0 |
| commit_gate | 49 | 62 | 0 | 0 |
| completion_gate | 2 | 52 | 45 | 0 |
| date_scope_guard | 435 | 7 | 0 | 0 |
| block_dangerous | 435 | 6 | 0 | 0 |
| send_gate | 0 | 6 | 0 | 0 |
| auto_compile | 1 | 0 | 0 | 0 |
| protect_files | 77 | 0 | 0 | 0 |
| risk_profile_prompt | 4 | 0 | 0 | 0 |
| stop_guard | 4 | 0 | 0 | 0 |
| unknown | 88 | 0 | 0 | 0 |
| write_marker | 18 | 0 | 0 | 0 |

## 판정 기준

- deny_rate_raw = deny 전체 / 승인요청 (가드레일 강도)
- deny_rate_effective = (deny - 오탐) / 승인요청 (실제 위반 비율)
- false_positive_rate = 오탐 / deny (높으면 잘못 막는 비율 높음)
- bypass_rate = 우회 / 승인요청 (0이어야 정상)
- 오탐 태깅: incident_ledger에서 false_positive=true 또는 classification=fp/오탐으로 표기
