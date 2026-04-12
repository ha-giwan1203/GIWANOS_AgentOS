# 스킬 아카이브 증적 — 2026-04-12

## 이동 사유
4축 분류(grade/수정일/커밋수/코드유무) 기준:
- 최종 수정 2026-03-31 (초기 생성 이후 미사용)
- git commit 2건 이하 (생성 + grade 일괄 반영만)
- 자동화 코드(*.py, *.sh) 없음 — SKILL.md만 존재하는 "기획 문서"

## 이동 내역

| 스킬명 | Grade | 원본 경로 | 목적지 |
|--------|-------|----------|--------|
| adversarial-review | C | 90_공통기준/스킬/adversarial-review/ | 98_아카이브/정리대기_20260412/스킬/ |
| cost-rate-management | B | 90_공통기준/스킬/cost-rate-management/ | 98_아카이브/정리대기_20260412/스킬/ |
| equipment-utilization | C | 90_공통기준/스킬/equipment-utilization/ | 98_아카이브/정리대기_20260412/스킬/ |
| hr-attendance | C | 90_공통기준/스킬/hr-attendance/ | 98_아카이브/정리대기_20260412/스킬/ |
| line-stoppage | C | 90_공통기준/스킬/line-stoppage/ | 98_아카이브/정리대기_20260412/스킬/ |
| partno-management | C | 90_공통기준/스킬/partno-management/ | 98_아카이브/정리대기_20260412/스킬/ |
| process-improvement | C | 90_공통기준/스킬/process-improvement/ | 98_아카이브/정리대기_20260412/스킬/ |
| procurement-delivery | C | 90_공통기준/스킬/procurement-delivery/ | 98_아카이브/정리대기_20260412/스킬/ |
| quality-assurance | C | 90_공통기준/스킬/quality-assurance/ | 98_아카이브/정리대기_20260412/스킬/ |
| quality-defect-report | C | 90_공통기준/스킬/quality-defect-report/ | 98_아카이브/정리대기_20260412/스킬/ |

## 로컬 실물 확인

```
98_아카이브/정리대기_20260412/스킬/
├── adversarial-review/          (SKILL.md)
├── adversarial-review.skill
├── cost-rate-management/        (SKILL.md)
├── cost-rate-management.skill
├── equipment-utilization/       (SKILL.md)
├── equipment-utilization.skill
├── hr-attendance/               (SKILL.md)
├── hr-attendance.skill
├── line-stoppage/               (SKILL.md)
├── line-stoppage.skill
├── partno-management/           (SKILL.md)
├── partno-management.skill
├── process-improvement/         (SKILL.md)
├── process-improvement.skill
├── procurement-delivery/        (SKILL.md)
├── procurement-delivery.skill
├── quality-assurance/           (SKILL.md)
├── quality-assurance.skill
├── quality-defect-report/       (SKILL.md)
└── quality-defect-report.skill
```

## 비고
- `98_아카이브/`는 `.gitignore`에 의해 Git 미추적
- 이 증적 파일이 Git 추적 경로(`90_공통기준/업무관리/운영검증/reports/`)에 이동 내역을 기록
- 원본 커밋: 58d5d1e7 (삭제) / 이 증적: 별도 커밋
- 복원 필요 시: `git checkout 58d5d1e7~1 -- "90_공통기준/스킬/{스킬명}/"` 또는 로컬 아카이브에서 복사
