---
name: line-batch-outer-main
description: ERP OUTER/MAIN 라인배치 자동화 — 검색 없이 그리드 행 순서대로 리스트업 처리
trigger: "OUTER 라인배치", "MAIN 라인배치", "아우터 배치", "메인 라인 배치", "SP3M3 라인배치", "리스트업 배치"
grade: A
---

# ERP OUTER/MAIN 라인배치 자동화

> 매핑 규칙 / JS 코드 / 실행 / 검증은 [MANUAL.md](MANUAL.md). 용어는 ../GLOSSARY.json.
> ERP URL: `http://erp-dev.samsong.com:19100/partLineBatchMng/viewPartLineBatchMng.do`

## 작업 분기
| 작업 | 함수 | ERP 화면 조건 |
|---|---|---|
| OUTER | `runOuterLine(startIdx)` | 라인구분=OUTER, 제품군=RETRACTOR |
| MAIN | `runMainLine(startIdx)` | 라인구분=MAIN, 조립라인=[SP3M3], 페이지당 10000건 |

## 동기화 제한 ⚠️
매시 x0:10~13 / x0:20~23 / x0:30~33 / x0:40~43 / x0:50~53 검색·저장 금지. `waitSync()` 자동 처리.

## 매핑 규칙 (요약)

### OUTER_RULES (v9) — row0 = SD9A01 고정 / row1+ 매핑
- WEBBING CUTTING → WABAS01 (WEBBING ASSY보다 먼저)
- WEBBING ASSY → WAMAS01
- D-RING → DRAAS11 / ANCHOR → ANAAS04 / SNAP ON → ANAAS04
- LASER MARKING → LTAAS01
- INNER BALL GUIDE / BASE LOCK / LOCKING / VEHICLE SENSOR / INNER SENSOR / TORSION ASSY → SUB LINE 無

### MAIN_RULES (v10) — LINE_DIV_NM1='MAIN' 행만, PART_TYPE_NM 기준
- 공정품_SUB → SWAMSMA
- SUB → SUB LINE 無
- row0/row1(OUTER행) 건드리지 않음

## 절차 (요약)
1. ERP 진입 + DevTools Console
2. STEP 1: JS 함수 등록 (MANUAL.md)
3. STEP 2: `window.runOuterLine(startIdx)` 또는 `runMainLine(startIdx)`
4. STEP 3: `lineStatus()` 진행 확인 / 중지 `_haltLine=true` / 재개

## verify
- `lineStatus()` done = total
- `_lineErrors` 빈 배열
- 무작위 3행 ERP 직접 확인
- OUTER: row0=SD9A01 / row1+ OUTER_RULES 일치
- MAIN: MAIN 행만 처리 / row0/row1 미변경 / 공정품_SUB→SWAMSMA, SUB→SUB LINE 無

## 핵심 주의
- `setLineCell` scrollColumn 후 350ms 대기 + Enter 키 커밋 필수 (blur는 isDirty=false)
- 상단 행 DOM 5회 재시도
- MAIN: PART_TYPE_NM 기준 (품명 아님)

## 실패 시
- DOM 5회 재시도 후 미발견 → 행 FAIL
- `setLineCell` 실패 → 행 FAIL
- 저장 timeout 30초 → 행 FAIL
- ERP 세션 만료 → 즉시 중단
- 되돌리기: ERP 비가역. `_lineLog` 보존 필수
- 상세 → MANUAL.md "실패 조건" + "되돌리기"
