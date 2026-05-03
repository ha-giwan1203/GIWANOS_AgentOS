---
name: assembly-cost-settlement
description: 월말 조립비 정산 자동화 — 대원테크(0109) 10개 라인 GERP/구ERP 합계 + 차이 유형 분류 + 보고서
trigger: "정산", "조립비", "settlement", "월마감 정산", "/settlement"
grade: B
---

# 조립비 정산 자동화

> 8단계 파이프라인 / 비즈니스 규칙 / 실패조건은 [MANUAL.md](MANUAL.md). 용어는 ../GLOSSARY.json.
> 도메인 규칙: `05_생산실적/조립비정산/CLAUDE.md`

## 절차 (요약)
1. 환경 세팅: `python setup_month.py {MM}` (월별 폴더 + 실적 복사 + config 갱신)
2. 파이프라인 실행: `python run_settlement_pipeline.py` (Step1~8)
3. step6 검증 PASS 확인 → 정산결과/오류리스트 엑셀 산출

## 8단계 파이프라인
| Step | 기능 |
|------|------|
| 1 | 파일검증 |
| 2 | GERP 처리 (주야 피벗) |
| 3 | 구ERP 처리 (전체업체 피벗) |
| 4 | 기준정보 매칭 |
| 5 | 정산 계산 |
| 6 | 합계 검증 (PASS/WARNING/FAIL) |
| 7 | 정산결과_MM월.xlsx (13시트) |
| 8 | 오류리스트_MM월.xlsx |

## verify
- step6 검증: 10개 라인 모두 PASS
- 00_정산집계 합계 = 라인별 합산
- GERP 총액 = 라인별 GERP 합산 (교차검증)
- 상세 → MANUAL.md "검증 항목"

## 실패 시
- 실적 파일 없음 / 기준정보 버전 불일치 / 단가 0원 → 중단
- `--start-from N --use-cache`로 실패 step부터 재실행
- 상세 → MANUAL.md "실패 조건" + "되돌리기" + RUNBOOK
