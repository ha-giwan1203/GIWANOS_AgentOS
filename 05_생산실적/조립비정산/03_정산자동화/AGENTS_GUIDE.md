# 조립비 정산 파이프라인 — 에이전트 운영 가이드

> 기준: 2026-03-24 실행 결과 기반 (02월 정산)
> 경로: `03_정산자동화/`

---

## 1. 파이프라인 개요

| Step | 스크립트 | 역할 | 평균 소요 |
|------|----------|------|----------|
| 1 | step1_파일검증.py | 입력 파일 3개 구조 검증 | ~5s |
| 2 | step2_gerp처리.py | GERP 대원테크 필터 + 주야 피벗 | ~2s |
| 3 | step3_구erp처리.py | 구ERP 필터 + 라인 매핑 | ~2s |
| 4 | step4_기준정보매칭.py | 기준정보 단가 매칭 | ~7s |
| 5 | step5_정산계산.py | 라인별 GERP/구ERP 정산 계산 | ~0.5s |
| 6 | step6_검증.py | 합계 일관성 + 비즈니스 규칙 검증 | ~0.2s |
| 7 | step7_보고서.py | 정산결과_MM월.xlsx 생성 | ~8s |

전체 소요: **약 25초**

---

## 2. 검수 기준표 (에이전트 판정 기준)

### 2-1. gerp-processor (Step 2 완료 후)

> 대상 파일: `_cache/step2_gerp.json`

| 항목 | PASS 조건 | 참고값 (02월) |
|------|-----------|--------------|
| `total_rows` | ≥ 1 (대원테크 행 수) | 2,885행 |
| `unmatched_lines` | `[]` (빈 배열) | [] |
| 라인 종류 | 10개 라인 모두 피벗에 존재 | SD9A01·SP3M3·WAMAS01·WABAS01·ANAAS04·DRAAS11·WASAS01·HCAMS02·HASMS02·ISAMS03 |
| 야간 라인 | SD9A01·SP3M3 야간품번 ≥ 1개 | SD9A01: 6개, SP3M3: 59개 |

PASS 판정: `unmatched_lines == []` AND `total_rows >= 1`

### 2-2. reference-matcher (Step 4 완료 후)

> 대상 파일: `_cache/step4_matched.json`

| 항목 | PASS 조건 | 참고값 (02월) |
|------|-----------|--------------|
| GERP 전체품번 | ≥ 1 | 1,256개 |
| 미매핑 품번 수 | 0 | 0개 |
| 매칭률 | 100% | 1256/1256 |

PASS 판정: `미매핑 == 0`

### 2-3. settlement-validator (Step 6 완료 후)

> 대상 파일: `_cache/step6_validation.json`

| 항목 | PASS 조건 | 참고값 (02월) |
|------|-----------|--------------|
| `overall` | `"PASS"` | PASS |
| `fail` | `0` | 0 |
| PASS 항목 수 | ≥ 5 | 5 |
| INFO 항목 수 | ≤ 2 (참고, 차단 아님) | 2 |

PASS 판정: `overall == "PASS"` AND `fail == 0`

**INFO 항목 목록 (차단 아님, 확인 권장)**:
- No.3 WABAS01 단가=0 품번: 56건 (실적있음: 3건) → 단가 등록 필요 여부 확인
- No.7 GERP vs 구ERP 라인별 차이: SD9A01·SP3M3 등 차이 발생 정상 (구ERP는 참고용)

### 2-4. report-writer (Step 7 완료 후)

> 대상 파일: `정산결과_MM월.xlsx`

| 항목 | PASS 조건 | 참고값 (02월) |
|------|-----------|--------------|
| 시트 수 | 13개 | 00_정산집계 + 10개 라인 + 01_차이분석 + 02_미매핑품번 |
| 미매핑 시트 행 수 | 0 | 0건 |
| 차이분석 행 수 | ≥ 0 | 529건 |

---

## 3. 실행 방법

```bash
# 기본 실행 (PYTHONUTF8=1 필수 — bash 환경)
PYTHONUTF8=1 python run_settlement_pipeline.py --month 02

# 특정 Step부터 재시작
PYTHONUTF8=1 python run_settlement_pipeline.py --start-from 5 --month 02

# 캐시 활용 (이미 처리된 Step 건너뜀)
PYTHONUTF8=1 python run_settlement_pipeline.py --use-cache --month 02
```

> Windows cmd 환경: `set PYTHONUTF8=1` 후 실행 시 콘솔 출력 깨짐 발생 가능.
> bash(Git Bash, WSL) 환경에서 실행 권장.

---

## 4. 주요 수치 참조 (02월 기준)

| 항목 | 수치 |
|------|------|
| GERP 전체 데이터 | 10,870행 |
| GERP 대원테크 | 2,885행 |
| 구ERP 전체 | 11,433행 |
| 구ERP 대원테크 | 1,116행 |
| GERP 정산 합계 | 194,591,630원 |
| 구ERP 정산 합계 | 110,364,430원 |
| GERP vs 구ERP 차이 | +84,227,200원 |

---

## 5. 에이전트 호출 판단 기준

| 에이전트 | 호출 시점 | 호출 생략 가능 조건 |
|----------|-----------|-------------------|
| gerp-processor | Step 2 완료 후 | `unmatched_lines == []` 확인 시 |
| reference-matcher | Step 4 완료 후 | 미매핑 0건 확인 시 |
| settlement-validator | Step 6 완료 후 | `fail == 0` 확인 시 항상 생략 가능 |
| report-writer | Step 7 완료 후 | 보고용 문서 정리 필요 시만 호출 |

> 파이프라인 정상 종료(전 Step SUCCESS) 시 에이전트 호출 없이 결과 직접 사용 가능.

---

## 6. 오류 대응

| 증상 | 원인 | 대응 |
|------|------|------|
| UnicodeEncodeError (cp949) | cmd에서 PYTHONUTF8 미적용 | bash 환경에서 `PYTHONUTF8=1 python ...` 실행 |
| Step 1 FAIL | 입력 파일 경로 불일치 | `_pipeline_config.py` 경로 확인 |
| Step 4 미매핑 발생 | 기준정보에 없는 신규 품번 | 기준정보 파일 업데이트 후 재실행 |
| config 복원 실패 | 비정상 종료 | `_pipeline_config.py.pipeline_bak` → 수동 복원 |
