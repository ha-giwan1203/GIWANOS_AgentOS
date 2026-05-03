---
name: line-batch-management
description: ERP 라인배치 관리 통합 자동화 — SP3메인서브 + OUTER 라인 (검색 기반 + 리스트업 기반). 시작 위치 확인 후 이어서 처리
trigger: "라인배치", "라인배치 입력", "라인배치 관리", "SUB ASSY 배치", "배치 설정", "ERP 배치", "품번 배치", "라인배치 작업", "배치 자동화"
grade: A
---

# ERP 라인배치 관리 자동화 (통합)

> 매핑 / JS 코드 / 절차 / 검증은 [MANUAL.md](MANUAL.md). 용어는 ../GLOSSARY.json.
> 분리 도구: `line-batch-mainsub` (메인서브) / `line-batch-outer-main` (OUTER/MAIN). 본 스킬은 통합 진입점.

## 작업 유형 분기
| 유형 | 함수 | 방식 |
|------|------|------|
| 메인서브 | `searchAndProcess` / `runQueue` | 품번 검색 |
| OUTER | `runOuterLine(startIdx)` | 리스트업 (검색 없이 그리드 순서) |

## 사전 준비
- ERP URL: `http://erp-dev.samsong.com:19100/partLineBatchMng/viewPartLineBatchMng.do`
- 기준품번 302개 내장 (2026-03-20 기준)
- **시작 위치 확인 필수**: 마지막 처리 품번/행번호 + 이어서 시작할 품번

## 동기화 제한 ⚠️
매시 x0:10~13 / x0:20~23 / x0:30~33 / x0:40~43 / x0:50~53 검색·저장 금지. `waitSyncClear()` 자동.

## 매핑 규칙 (요약)

### 메인서브 (LINE_RULES) — row0=OUTER_LINE_CD / row1=SP3M3 / row2+ 매핑
- HOLDER,CLR ASSY → HCAMS02 (먼저 체크)
- WEBBING CUTTING → WABAS01 (WEBBING ASSY보다 먼저)
- WEBBING ASSY → WAMAS01
- INNER BALL GUIDE / BASE LOCK / LOCKING / INNER SENSOR ASSY → SUB LINE 無

### OUTER (OUTER_RULES) — row0=SD9A01 / row1+ 매핑
- WEBBING CUTTING → WABAS01 / WEBBING ASSY → WAMAS01
- D-RING → DRAAS11 / ANCHOR ASSY → ANAAS04 / SNAP-ON → ANAAS04
- LASER MARKING → LTAAS01

## 절차 (요약)
1. ERP 진입 + DevTools Console + 시작 위치 확인
2. JS 함수 등록 (MANUAL.md 코드)
3. 작업 유형별 실행:
   - 메인서브: `window.runQueue()`
   - OUTER: `window.runOuterLine(startIdx)`
4. 진행 확인 / 중지 / 재개

## verify
- `_queueSummary` 또는 `lineStatus()` err = 0
- 처리 완료 = 대상 품번/행 수
- 무작위 3개 ERP 직접 확인

## 실패 시
- DOM 미발견 3~5회 → 행 FAIL + `_processErrors`/`_lineErrors`
- 저장 timeout → 행 FAIL
- ERP 세션 만료 → 즉시 중단 (`_haltAll`/`_haltLine = true`)
- 되돌리기: ERP 비가역. 변경 행 추적 후 수동
- 상세 → MANUAL.md "실패 조건" + "되돌리기"
