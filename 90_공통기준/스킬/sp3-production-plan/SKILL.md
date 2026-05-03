---
name: sp3-production-plan
description: SP3 생산계획 자동화 — ERP 계획 반영, D+1/D+2 산출, 야간 이월, 수동서열 반영
version: v3.0
trigger: "생산계획", "SP3 계획", "생산지시서", "APPLY_TO_PLAN", "야간 이월", "수동서열"
grade: B
---

# SP3 생산계획 자동화

> 상세 절차/규칙/되돌리기는 [MANUAL.md](MANUAL.md). 용어는 ../GLOSSARY.json.

## 절차 (요약)
1. ERP 계획 Sheet2 붙여넣기
2. Sheet3에 D+1/D+2 현재고 입력
3. 매크로 `APPLY_TO_PLAN` 실행
4. Sheet4 야간/주간 반영 확인
5. 필요 시 수동서열(V/W열) → `APPLY_MANUAL_SEQ`

## 핵심 규칙 (1줄 요약)
- 야간 = 행 3~100 (3,900EA 한도) / 주간 = 행 104~203
- 수식열(C,D,F,H~S,K,M) 직접 수정 금지 — 매크로는 B/E/G/T만 사용
- 자동 정렬 13단계 (SUB 823 마지막 → 8PI/10PI → ... → 동률 원본 유지)

## verify
- B/E/G/T열만 변경 + K/M 수식 보존
- V/W 자동 초기화 + 823 마지막 정렬 유지
- 상세 검증 항목 → MANUAL.md "검증 항목"

## 실패 시
- 수식열 파괴 감지 → 즉시 중단
- RESTORE_PLAN 매크로로 PLAN_BACKUP_FIXED 시트에서 복원
- 상세 → MANUAL.md "실패 조건" + "되돌리기"
