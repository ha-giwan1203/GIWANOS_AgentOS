# Skill Contract Gap Report

- 검사 대상: 27개
- PASS: 6개 (자동화 완성 스킬)
- FAIL: 21개 (미자동화 스킬 포함, 의도적 제외 대상 다수)

## 스킬 3등급 분류

| 등급 | 정의 | 수량 |
|------|------|------|
| A (실행형) | 브라우저/ERP/MES/API 직접 조작 | 7개 |
| B (파일수정형) | 엑셀/코드/문서 생성·수정 | 8개 |
| C (분석형) | 읽기 전용 분석·보고 | 12개 |

## Grade 경고

- WARN: adversarial-review: grade 필드 없음 (기대값: C)
- WARN: assembly-cost-settlement: grade 필드 없음 (기대값: B)
- WARN: cdp-wrapper: grade 필드 없음 (기대값: A)
- WARN: chomul-module-partno: grade 필드 없음 (기대값: A)
- WARN: cost-rate-management: grade 필드 없음 (기대값: B)
- WARN: equipment-utilization: grade 필드 없음 (기대값: C)
- WARN: flow-chat-analysis: grade 필드 없음 (기대값: C)
- WARN: hr-attendance: grade 필드 없음 (기대값: C)
- WARN: line-batch-mainsub: grade 필드 없음 (기대값: A)
- WARN: line-batch-management: grade 필드 없음 (기대값: A)
- WARN: line-batch-outer-main: grade 필드 없음 (기대값: A)
- WARN: line-mapping-validator: grade 필드 없음 (기대값: B)
- WARN: line-stoppage: grade 필드 없음 (기대값: C)
- WARN: night-scan-compare: grade 필드 없음 (기대값: B)
- WARN: partno-management: grade 필드 없음 (기대값: C)
- WARN: pptx-generator: grade 필드 없음 (기대값: B)
- WARN: process-improvement: grade 필드 없음 (기대값: C)
- WARN: procurement-delivery: grade 필드 없음 (기대값: C)
- WARN: production-report: grade 필드 없음 (기대값: B)
- WARN: production-result-upload: grade 필드 없음 (기대값: A)
- WARN: quality-assurance: grade 필드 없음 (기대값: C)
- WARN: quality-defect-report: grade 필드 없음 (기대값: C)
- WARN: skill-creator-merged: grade 필드 없음 (기대값: C)
- WARN: sp3-production-plan: grade 필드 없음 (기대값: B)
- WARN: supanova-deploy: grade 필드 없음 (기대값: B)
- WARN: youtube-analysis: grade 필드 없음 (기대값: C)
- WARN: zdm-daily-inspection: grade 필드 없음 (기대값: A)

## FAIL 목록

### [C] 90_공통기준\스킬\adversarial-review\SKILL.md
- 누락: ## 실패 조건, ## 중단 기준, ## 검증 항목, ## 되돌리기 방법

### [A] 90_공통기준\스킬\cdp-wrapper\SKILL.md
- 누락: ## 실패 조건, ## 중단 기준, ## 검증 항목, ## 되돌리기 방법

### [B] 90_공통기준\스킬\cost-rate-management\SKILL.md
- 누락: ## 실패 조건, ## 중단 기준, ## 검증 항목, ## 되돌리기 방법

### [C] 90_공통기준\스킬\equipment-utilization\SKILL.md
- 누락: ## 실패 조건, ## 중단 기준, ## 검증 항목, ## 되돌리기 방법

### [C] 90_공통기준\스킬\flow-chat-analysis\SKILL.md
- 누락: ## 실패 조건, ## 중단 기준, ## 검증 항목, ## 되돌리기 방법

### [C] 90_공통기준\스킬\hr-attendance\SKILL.md
- 누락: ## 실패 조건, ## 중단 기준, ## 검증 항목, ## 되돌리기 방법

### [A] 90_공통기준\스킬\line-batch-mainsub\SKILL.md
- 누락: ## 실패 조건, ## 중단 기준, ## 검증 항목, ## 되돌리기 방법

### [A] 90_공통기준\스킬\line-batch-outer-main\SKILL.md
- 누락: ## 실패 조건, ## 중단 기준, ## 검증 항목, ## 되돌리기 방법

### [C] 90_공통기준\스킬\line-stoppage\SKILL.md
- 누락: ## 실패 조건, ## 중단 기준, ## 검증 항목, ## 되돌리기 방법

### [C] 90_공통기준\스킬\partno-management\SKILL.md
- 누락: ## 실패 조건, ## 중단 기준, ## 검증 항목, ## 되돌리기 방법

### [B] 90_공통기준\스킬\pptx-generator\SKILL.md
- 누락: ## 실패 조건, ## 중단 기준, ## 검증 항목, ## 되돌리기 방법

### [C] 90_공통기준\스킬\process-improvement\SKILL.md
- 누락: ## 실패 조건, ## 중단 기준, ## 검증 항목, ## 되돌리기 방법

### [C] 90_공통기준\스킬\procurement-delivery\SKILL.md
- 누락: ## 실패 조건, ## 중단 기준, ## 검증 항목, ## 되돌리기 방법

### [B] 90_공통기준\스킬\production-report\SKILL.md
- 누락: ## 실패 조건, ## 중단 기준, ## 검증 항목, ## 되돌리기 방법

### [C] 90_공통기준\스킬\quality-assurance\SKILL.md
- 누락: ## 실패 조건, ## 중단 기준, ## 검증 항목, ## 되돌리기 방법

### [C] 90_공통기준\스킬\quality-defect-report\SKILL.md
- 누락: ## 실패 조건, ## 중단 기준, ## 검증 항목, ## 되돌리기 방법

### [C] 90_공통기준\스킬\skill-creator-merged\SKILL.md
- 누락: ## 실패 조건, ## 중단 기준, ## 검증 항목, ## 되돌리기 방법

### [B] 90_공통기준\스킬\sp3-production-plan\SKILL.md
- 누락: ## 실패 조건, ## 중단 기준, ## 검증 항목, ## 되돌리기 방법

### [B] 90_공통기준\스킬\supanova-deploy\SKILL.md
- 누락: ## 실패 조건, ## 중단 기준, ## 검증 항목, ## 되돌리기 방법

### [C] 90_공통기준\스킬\youtube-analysis\SKILL.md
- 누락: ## 실패 조건, ## 중단 기준, ## 검증 항목, ## 되돌리기 방법

### [A] 90_공통기준\스킬\zdm-daily-inspection\SKILL.md
- 누락: ## 실패 조건, ## 중단 기준, ## 검증 항목, ## 되돌리기 방법

## PASS 목록

- [B] 90_공통기준\스킬\assembly-cost-settlement\SKILL.md
- [A] 90_공통기준\스킬\chomul-module-partno\SKILL.md
- [A] 90_공통기준\스킬\line-batch-management\SKILL.md
- [B] 90_공통기준\스킬\line-mapping-validator\SKILL.md
- [B] 90_공통기준\스킬\night-scan-compare\SKILL.md
- [A] 90_공통기준\스킬\production-result-upload\SKILL.md
