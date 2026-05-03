---
name: line-batch-mainsub
description: ERP 메인서브 라인배치 자동화 — SP3메인서브 품번 검색 + SUB ASSY 그리드 조립라인 자동 입력 + 저장. 302개 기준품번 내장
trigger: "메인서브 라인배치", "메인서브 배치", "SP3 품번 배치", "품번 검색 배치", "메인서브 자동화"
grade: A
---

# ERP 메인서브 라인배치 자동화

> 매핑 규칙 / JS 코드 / 실행 / 검증은 [MANUAL.md](MANUAL.md). 용어는 ../GLOSSARY.json.
> ERP URL: `http://erp-dev.samsong.com:19100/partLineBatchMng/viewPartLineBatchMng.do`

## 동기화 제한 ⚠️
매시 x0:10~13, x0:20~23, x0:30~33, x0:40~43, x0:50~53 검색·저장 금지. `waitSyncClear()` 자동 처리.

## 행별 처리
| 행 | 처리 |
|---|---|
| row0 | OUTER_LINE_CD (공란이면 최빈값 fallback) |
| row1 | SP3M3 고정 |
| row2+ | LINE_RULES 매핑 (해당 없으면 SKIP) |

## 매핑 규칙 (LINE_RULES) — 우선순위
1. **PART_TYPE_NM**: 공정품_SUB → SWAMS04
2. **MBOM_PART_NM 포함**:
   - HOLDER,CLR ASSY → HCAMS02 (먼저 체크)
   - HOLDER ALR SENSOR ASSY → HASMS02
   - WEBBING CUTTING → WABAS01 (WEBBING ASSY보다 먼저)
   - WEBBING ASSY → WAMAS01
   - RETRACTION SPRING / INNER BALL GUIDE / BASE LOCK / LOCKING / VEHICLE SENSOR / INNER SENSOR ASSY → SUB LINE 無

## 절차 (요약)
1. ERP 페이지 진입 → DevTools Console
2. STEP 1 JS 함수 등록 (MANUAL.md 코드)
3. STEP 2 실행: `window.runQueue()` 또는 특정 품번부터 이어서
4. STEP 3 진행 확인 / 중지(`_haltAll=true`) / 재개

## verify
- `_queueSummary` `err` 합계 0
- 처리 완료 = `_prodQueue.length`
- `_processErrors` 빈 배열
- 무작위 3개 품번 ERP 직접 확인 (ASSY_LINE_NM 정상)

## 실패 시
- 검색 0건 → SKIP (전체 FAIL 아님)
- DOM 미발견 3회 → 행 FAIL + `_processErrors` 기록
- 저장 timeout 10초 → 행 FAIL
- ERP 세션 만료 → 즉시 중단 (`_haltAll=true`)
- 되돌리기: ERP 저장 비가역. 변경 행은 `_processLog` 추적 후 수동
- 상세 → MANUAL.md "실패 조건" + "되돌리기"
