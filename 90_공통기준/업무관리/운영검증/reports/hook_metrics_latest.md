# Hook 4지표 집계

- 생성시각: 2026-04-08T22:10:28+09:00
- hook_log: 3444건 / incident_ledger: 82건

## 합계

| 지표 | 건수 | 비율 |
|------|------|------|
| 승인 요청 (hook 발화) | 1268 | - |
| deny (raw) | 82 | 6.47% |
| deny (effective, 오탐 제외) | 37 | 2.92% |
| 오탐 (false_positive) | 45 | 54.88% |
| 우회 감지 | 0 | 0.00% |

## hook별 상세

| hook | 발화 | deny | 오탐 | 우회 |
|------|------|------|------|------|
| completion_gate | 0 | 45 | 45 | 0 |
| commit_gate | 80 | 25 | 0 | 0 |
| block_dangerous | 489 | 6 | 0 | 0 |
| date_scope_guard | 489 | 4 | 0 | 0 |
| evidence_gate | 0 | 1 | 0 | 0 |
| send_gate | 0 | 1 | 0 | 0 |
| protect_files | 210 | 0 | 0 | 0 |

## 판정 기준

- deny_rate_raw = deny 전체 / 승인요청 (가드레일 강도)
- deny_rate_effective = (deny - 오탐) / 승인요청 (실제 위반 비율)
- false_positive_rate = 오탐 / deny (높으면 잘못 막는 비율 높음)
- bypass_rate = 우회 / 승인요청 (0이어야 정상)
- 오탐 태깅: incident_ledger에서 false_positive=true 또는 classification=fp/오탐으로 표기
