---
name: gerp-unregistered-check
description: 매월 정산 빌더 산출물(정산_수식버전_MM월.xlsx)에서 GERP 미등록 품번 + 분류 라벨 정확성 + ERP 정정 가이드 자동 산출. 빌더 신뢰성 검증 + 사용자 ERP 정정 워크플로우 진입점.
trigger: "GERP 미등록", "미등록 품번", "오류리스트 검증", "라벨 검증", "GERP 정정", "/gerp-unregistered MM"
grade: B
---

# GERP 미등록 품번 확인 (월 마감 정산 후)

> 상세 절차·결함 후보·분류 정의·실패조건은 [MANUAL.md](MANUAL.md). 도메인 룰: `05_생산실적/조립비정산/CLAUDE.md`.
> 세션148(2026-05-08) 신설. 4월 정산 사용자 신뢰 회복 검증으로 정착.

## 절차 (요약)

```bash
cd 90_공통기준/스킬/gerp-unregistered-check
python run_check.py {MM}        # 예: python run_check.py 04
```

내부 흐름 (자동):
1. 본체 복사 → `정산_수식버전_{MM}월_VALUES.xlsx` (값변환 사본, 본체 보존)
2. Excel COM `CalculateFull` → 수식 → 정적값 일괄 변환
3. `verify_error_labels.py` 실행 — 라벨 정확성 + 카테고리 분류 + vendor 분포
4. 산출물 (`05_생산실적/조립비정산/{MM+1}월/오류리스트_재검증_{YYYYMMDD}/`)

## 산출물

**저장 위치**: `05_생산실적/조립비정산/{MM+1}월/오류리스트_재검증_{YYYYMMDD}/` (정산 도메인 작업폴더 내부)

| 파일 | 역할 |
|------|------|
| `verify_summary.md` | 4종 통과기준 + 카테고리 분포 + vendor 정밀 분류 |
| `mismatch_rows.xlsx` | 라벨불일치/매핑불일치/미매칭/catchall 4시트 |
| `category_distribution.csv` | 6 internal × 5 user 카테고리 분포 |
| `vendor_analysis.csv` | GERP누락 vendor 정밀 분류 (5종) |
| `정산_수식버전_{MM}월_VALUES.xlsx` | 본체 수식→값 변환 사본 |
| `오류리스트_{MM}월_GERP확인완료.xlsx` | ERP 자동 조회 결과 박힌 양식 (collect_gerp_status.py 산출) |
| `erp_gerp_status_raw_{MM}월.json` | ERP API raw 응답 캐시 |

## verify (Phase E 통과기준 4종)

1. 라인시트 빌더라벨 ≡ 재산출라벨 (불일치 0)
2. 오류리스트 매핑 정합 (매핑 불일치 0 + 미매칭 0)
3. Coverage (라인시트 차이≠0 행 ≡ 오류리스트 행)
4. 합계 정합 (정산집계 ≡ 오류리스트)

4/4 PASS = 빌더 정상. 사용자 신뢰 회복 + ERP 정정 진행 가능.

## GERP누락 vendor 5종 분류 (사용자 ERP 정정 가이드용)

| 분류 | 의미 | ERP 정정 |
|------|------|---------|
| GERP raw 부재 | 대원테크 4월 GERP 미등록 | 신규 단가 등록 |
| 같은라인 0109 | 같은 라인+0109 (드뭄) | 라인시트 SUMIFS 결함 가능 — 빌더 점검 |
| 같은라인 비0109 | 같은 라인+협력사 분리 | 협력사 분리 룰 적용 |
| 다른라인만 | 다른 라인엔 등록됨 | 라인 추가 등록 (예: ANAAS04 89870BS500OVS — SD9A01에 등록) |
| 빈vendor | vendor 컬럼 빈 | 데이터 결함 — raw 점검 |

## ERP 정정 시간 제약 ⚠️

GERP 매시 5구간 조회 차단: `x0:10~13, x0:20~23, x0:30~33, x0:40~43, x0:50~53`
정시(x0:00~03)는 가용. 라인배치 지침 권위 (`10_라인배치/CLAUDE.md:45`).
ERP 진입 전 시간 체크 필수.

## 실패 시

- 본체 락 (`~$정산_수식버전_MM월.xlsx`) → 사용자 Excel에서 닫고 재실행
- pywin32 미설치 → `pip install pywin32` 후 재실행
- VALUES 사본이 사용자 본체보다 오래됨 → `python run_check.py {MM} --force` 재생성
- 상세 → MANUAL.md "실패 조건"
