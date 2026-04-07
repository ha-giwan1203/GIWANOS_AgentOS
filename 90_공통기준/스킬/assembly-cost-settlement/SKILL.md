---
name: assembly-cost-settlement
description: >
  월말 조립비 정산 자동화 스킬.
  "정산", "조립비", "settlement", "월마감 정산", "정산 실행" 등을 언급하면 이 스킬을 사용할 것.
  GERP/구ERP 실적 데이터를 기반으로 대원테크(0109) 10개 라인의 조립비 정산을 자동 수행한다.
  환경 세팅 → 8단계 파이프라인 → 오류 리스트 → 검증 보고까지 원스텝으로 처리.
---

# 조립비 정산 자동화

## 목적
매월 반복되는 조립비 정산 업무를 자동화한다.
GERP/구ERP 실적 데이터에서 10개 라인의 정산금액을 계산하고,
차이 원인을 유형별로 분류하여 정산결과 보고서와 오류 리스트를 생성한다.

## 기본 설정
- **대상 업체**: 대원테크 (0109)
- **10개 라인**: SD9A01, SP3M3, WAMAS01, WABAS01, ANAAS04, DRAAS11, WASAS01, HCAMS02, HASMS02, ISAMS03
- **기준정보**: `01_기준정보/기준정보_라인별정리_최종_V1_20260316.xlsx`
- **파이프라인**: `03_정산자동화/run_settlement_pipeline.py`
- **슬래시 명령**: `/settlement MM` (예: `/settlement 03`)

## 실행 전 확인사항
- `04_실적데이터/`에 해당 월 GERP/구ERP 파일이 존재해야 함
  - GERP 파일명 패턴: `G-ERP {N}월실적.xlsx`
  - 구ERP 파일명 패턴: `구ERP {N}월 실적.xlsx`
- Python 3.12 + pandas + openpyxl 설치
- 기준정보 파일 최신 버전 확인

## 워크플로우

### Phase 1: 환경 세팅 (`setup_month.py`)
```bash
python setup_month.py {MM}
```
- 월별 폴더 생성: `{MM+1}월/실적데이터/`, `{MM+1}월/_cache/`
- 실적 파일 탐색 → 복사 (04_실적데이터/ → 월별 폴더)
- `_pipeline_config.py` 자동 수정 (경로, MONTH, OLDERP_SHEET)
- `--dry-run`으로 사전 확인 가능

### Phase 2: 파이프라인 실행 (8단계)
```bash
python run_settlement_pipeline.py
# 또는 특정 step부터:
python run_settlement_pipeline.py --start-from 5 --use-cache
```

| Step | 스크립트 | 기능 |
|------|---------|------|
| 1 | step1_파일검증.py | 파일 존재 + 시트 구조 검증 |
| 2 | step2_GERP처리.py | GERP 필터 + 주야 피벗 + RSP 역변환 |
| 3 | step3_구erp처리.py | 구ERP 필터 + 전체업체 피벗 + 지원분 |
| 4 | step4_기준정보매칭.py | 단가 매칭 + 미매핑 검출 |
| 5 | step5_정산계산.py | 라인별 GERP/구ERP 정산 계산 |
| 6 | step6_검증.py | 합계 검증 (PASS/WARNING/FAIL) |
| 7 | step7_보고서.py | 정산결과_MM월.xlsx 생성 (13개 시트) |
| 8 | step8_오류리스트.py | 오류리스트_MM월.xlsx 생성 |

### Phase 3: 결과 검증
- step6 검증 결과 확인 (PASS/WARNING/FAIL)
- 라인별 정산금액 대조
- 오류 유형별 건수/금액 요약

## 핵심 비즈니스 규칙

### 야간 계산 (구ERP 방식 통일)
- SD9A01: 야간금액 = 야간수량 x 기준단가 x 1.3
- SP3M3: 야간금액 = 야간수량 x 170원 (고정단가)
- SUB 라인: 야간 없음

### GERP 주야 분리
- 정상행 = 총수량 (주간+야간), 추가행 = 야간수량
- 순수 주간 = 정상수량 - 추가수량 (SD9A01만)

### 구ERP 피벗
- SD9A01: 전체업체 피벗 (지원분 포함)
- SP3M3: 전체업체 피벗 (모듈품번 기준)
- SUB: 전체업체 피벗

### 오류 유형
| 유형 | 조건 |
|------|------|
| 구실적누락 | GERP에만 실적 |
| GERP누락 | 구ERP에만 실적 |
| 기준누락 | 단가 없음 |
| 수량차이 | 수량 불일치 |
| 정산차이 | 금액만 불일치 |

## 산출물
| 파일 | 위치 | 내용 |
|------|------|------|
| 정산결과_MM월.xlsx | {월별폴더}/ | 00_정산집계 + 10개 라인 시트 + 차이분석 + 검증결과 + 오류리스트 |
| 오류리스트_MM월.xlsx | {월별폴더}/ | DB 양식 오류 리스트 + 유형별 요약 |
| _cache/*.json | {월별폴더}/_cache/ | step1~5 중간 결과 |

## 실패 시 대응
- `03_정산자동화/RUNBOOK.md` 참조
- `run_logs/` 최신 `_summary.json`에서 `failed_step` 확인
- `--start-from N --use-cache`로 실패 step부터 재실행

## 실패 조건
- step1 파일검증에서 GERP/구ERP 파일 미존재 또는 시트 구조 불일치
- step4 기준정보매칭에서 미매핑 품번이 전체의 10% 이상
- step6 검증에서 FAIL 판정 (합계 불일치)
- `_summary.json`의 `failed_step`이 null이 아닌 경우

## 중단 기준
- 실적 파일이 없으면 즉시 중단 (Phase 1에서 차단)
- 기준정보 파일 버전이 최신이 아니면 사용자 확인 전까지 중단
- step5 계산 중 라인 단가가 0원인 품번 발견 시 중단 → 기준정보 점검
- 파이프라인 중간 step에서 예외 발생 시 해당 step에서 중단 (캐시 보존)

## 검증 항목
- step6 검증 결과: 10개 라인 모두 PASS 여부
- 정산결과 엑셀 13개 시트 존재 + 00_정산집계 합계 = 라인별 합산
- 오류리스트 건수/금액이 차이분석 시트와 일치
- GERP 총액 = 라인별 GERP 합산 (교차검증)

## 되돌리기 방법
- `--start-from N --use-cache`로 실패 step부터 재실행
- `_cache/*.json` 삭제 후 전체 재실행 (클린 런)
- 기준정보 파괴 시: `01_기준정보/` 백업에서 복원 후 step4부터 재실행
- 상세 복구 절차: `03_정산자동화/RUNBOOK.md` 참조

## 관련 문서
- 도메인 규칙: `05_생산실적/조립비정산/CLAUDE.md`
- 파이프라인 계약: `03_정산자동화/pipeline_contract.md`
- 에이전트 가이드: `03_정산자동화/AGENTS_GUIDE.md`
- 실패 복구: `03_정산자동화/RUNBOOK.md`
