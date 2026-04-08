# Hook 4지표 집계

- 생성시각: 2026-04-08T21:19:57+09:00
- hook_log: 2918건 / incident_ledger: 80건

## 합계

| 지표 | 건수 | 비율 |
|------|------|------|
| 승인 요청 (hook 발화) | 1006 | - |
| deny (차단) | 80 | 7.95% |
| 오탐 (false_positive) | 0 | 0.00% |
| 우회 감지 | 0 | 0.00% |

## hook별 상세

| hook | 발화 | deny | 오탐 | 우회 |
|------|------|------|------|------|
| completion_gate | 1 | 45 | 0 | 0 |
| commit_gate | 64 | 23 | 0 | 0 |
| block_dangerous | 371 | 6 | 0 | 0 |
| date_scope_guard | 371 | 4 | 0 | 0 |
| evidence_gate | 0 | 1 | 0 | 0 |
| send_gate | 0 | 1 | 0 | 0 |
| protect_files | 198 | 0 | 0 | 0 |
| write_marker | 1 | 0 | 0 | 0 |

## 판정 기준

- deny_rate = deny / 승인요청 (높으면 규칙이 너무 엄격)
- false_positive_rate = 오탐 / deny (높으면 잘못 막는 비율 높음)
- bypass_rate = 우회 / 승인요청 (0이어야 정상)
- 오탐 태깅: incident_ledger에서 false_positive=true 또는 classification=fp/오탐으로 표기
