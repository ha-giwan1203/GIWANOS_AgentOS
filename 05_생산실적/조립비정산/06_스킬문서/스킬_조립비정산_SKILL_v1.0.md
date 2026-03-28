---
name: assembly-cost-settlement
description: 조립비 정산 자동화 스킬. 매월 GERP 실적 파일과 구ERP 실적 파일을 읽어서 대원테크(업체코드 0109) 조립비 정산 DB를 자동으로 채우고, 요약 및 상세 분석 Excel 리포트를 생성한다. '정산', '조립비', 'GERP', '구ERP', '대원테크', '월마감', '실적 집계', '라인별 정산', '정산금액', '차이 분석' 등의 키워드가 포함된 요청에 반드시 이 스킬을 사용할 것. 매월 반복되는 조립비 정산 업무 전체를 자동화하는 스킬이므로, 사용자가 새로운 달의 파일을 업로드하거나 정산 관련 작업을 요청하면 항상 이 스킬을 참조할 것.
---

# 조립비 정산 자동화 (파이프라인 v2)

## 개요
대원테크(업체코드 0109) 조립비 정산을 7단계 파이프라인으로 자동화한다.
Python이 전체 계산 → 값만 엑셀에 기록 (수식 없음). 실행 시간 약 29초.

## 프로젝트 경로
```
C:\Users\User\Desktop\업무리스트\05_생산실적\조립비정산\
├── 01_기준정보\   기준정보_라인별정리_최종_V1_20260316.xlsx
├── 02_정산DB\     조립비_관리DB_02월_20260311.xlsx
├── 03_정산자동화\  run_settlement_pipeline.py (메인)
├── 04_실적데이터\  GERP_실적현황, 구ERP_실적현황
├── 05_보고서\     GERP_구ERP_품번대조보고
├── CLAUDE.md      정산 작업 규칙
└── STATUS.md      진행 현황
```

## 실행 방법
```bash
cd 05_생산실적/조립비정산/03_정산자동화
PYTHONUTF8=1 python run_settlement_pipeline.py
```

월 변경 시: `_pipeline_config.py`의 `MONTH`, `OUTPUT_FILE`, 실적 파일 경로 수정.

## 설정 파일: _pipeline_config.py
| 변수 | 용도 |
|------|------|
| MASTER_FILE | 기준정보 파일 경로 |
| GERP_FILE | GERP 실적 파일 경로 |
| OLDERP_FILE | 구ERP 실적 파일 경로 |
| OUTPUT_FILE | 정산결과 엑셀 출력 경로 |
| MONTH | 정산 월 |
| LINE_ORDER | 10개 라인 순서 |
| LINE_INFO | 라인별 이름/유형/야간여부 |
| GERP_COL / OLDERP_COL / MASTER_COL | 컬럼 인덱스 |

## 파이프라인 7단계

### Step 1: 파일 검증 (step1_파일검증.py)
- 입력 파일 존재 확인
- 시트 구조, 컬럼 수, 데이터행 수 검증
- GERP 주야구분 값(정상/추가) 확인
- 출력: _cache/step1_validation.json

### Step 2: GERP 처리 (step2_gerp처리.py)
- GERP 실적에서 대원테크(0109) 필터
- 주야구분: '정상'→주간, '추가'→야간
- **라인별 품번-수량 피벗**: `groupby('product_no')['qty'].sum()`
- **라인별 품번-금액 피벗**: `groupby('product_no')['amount'].sum()` (GERP 원본금액 보존)
- **GERP 조립품번 lookup**: `(라인|품번|단가) → 조립품번` (col12)
- 출력: _cache/step2_gerp.json (day_pivot, night_pivot, day_amt_pivot, night_amt_pivot, gerp_assy_lookup)

### Step 3: 구ERP 처리 (step3_구erp처리.py)
- 구ERP Sheet1에서 대원테크(0109) 필터
- 라인코드 매핑: TD9→SD9A01, SP3S03→SP3M3, D9N6→SD9A01
- LOTNO 끝자리: B=야간, 나머지=주간
- 출력: _cache/step3_olderp.json

### Step 4: 기준정보 매칭 (step4_기준정보매칭.py)
- 기준정보 파일 라인별 시트에서 대원테크(0109) 품번 로딩
- **조립품번(D열) 추출**: 기준정보 형식 `ANAAS04-01040`
- **동일품번-동일단가 중복 제거**
  - 같은 (part_no, price) 조합이 2행 이상이면 첫 번째만 유지
  - 다른 단가(다중단가)는 정상 — 행별 개별 유지
- RSP 모듈품번 역추적
- GERP 품번 vs 기준정보 매칭율 확인
- 출력: _cache/step4_matched.json (각 row에 assy_part 포함)

### Step 5: 정산 계산 (step5_정산계산.py)
- 기준정보 master × GERP 피벗 × 구ERP 피벗 조인
- **조립품번 매핑**: 기준정보 조립품번 우선, 없으면 GERP 조립품번 fallback
- 금액 계산: 기준단가 × 수량 (기준단가가 권위값)
- 야간 가산: calc_night_price() — SD9A01은 30% 가산, SP3M3은 170원 고정
- **GERP 원본금액 필드**: gerp_orig_day_amt, gerp_orig_ngt_amt (비교/검증용)
- **SP3M3 구ERP**: 전체업체 피벗 사용 (모듈품번 매칭 불가), 구ERP야간=GERP야간 동일 적용
- 출력: _cache/step5_settlement.json (items에 assy_part 포함)

### Step 6: 검증 (step6_검증.py)
- 전체합계 일관성, SD9A01 단가기준판정, Usage=2 짝수 검증
- SP3M3 야간 고정단가 170원 적용 확인
- GERP 미매핑 품번 현황
- 출력: _cache/step6_validation.json

### Step 7: 보고서 생성 (step7_보고서.py)
- **00_정산집계 시트**:
  - 상단: 라인별 GERP 주간/야간 수량·금액, 정산합계, GERP원본금액, 차이
  - 하단: GERP vs 구ERP 주야 분리 비교 14컬럼 (GERP주간qty/amt, GERP야간qty/amt, GERP합계, 구ERP주간qty/amt, 구ERP야간qty/amt, 구ERP합계, 차이)
- **라인별 상세 시트 10개**:
  - 기본정보(6): No, 품번, 조립품번, Usage, 기준단가, GERP단가
  - GERP정산: 수량/금액 (야간라인은 주야분리+합계)
  - 구ERP비교: 수량/금액 (야간라인은 주야분리)
  - 결과(3): 수량차, 금액차, 유형
  - 0값→하이픈, 실적없는행→숨김, 합계행 전컬럼
  - GERP단가: 동일품번 다중단가 지원 (기준단가 매칭)
  - 유형: G실적누락/구실적누락/기준누락/다중단가/단가+수량/단가차이/수량차이/정산차이
- **01_차이분석 시트**: 차이 발생 품번 전체 + 라인별 소계
  - 컬럼: 라인, 품번, 기준단가 / GERP주간qty·amt·야간qty·합계amt / 구ERP주간qty·amt·야간qty·합계amt / 수량차 / 금액차 / **유형** / 비고
  - 유형 자동 판정 (G실적누락/구실적누락/기준누락/다중단가/단가+수량/단가차이/수량차이/정산차이)
  - 라인별 소계 행 자동 생성
- **02_미매핑품번 시트**: GERP에만 있는 품번
- 출력: 정산결과_{월}월.xlsx

## 핵심 비즈니스 규칙

### 단가 체계
- 기준정보 단가가 권위값. GERP 자체 단가와 다를 수 있다
- 동일품번-다중단가: 행별 개별 계산 후 합산 (정상)
- 동일품번-동일단가 중복: step4에서 자동 제거 (기준정보 오류)

### 야간 정산
- SD9A01: 전체에 100% 적용 + 야간분에 30% 추가 가산
- SP3M3: 야간 고정단가 170원
- SD9A01 단가기준판정: GERP단가 ≤500 → 야간가산, >500 → 기본

### SP3M3 야간 모듈품번(RSP) 역변환
- GERP SP3M3 야간("추가")행 품번은 RSP 모듈품번 = 야간 추가수당
- 매핑: 1차 `03_품번관리/초물관리/SP3M3_모듈품번_최신.xlsx` + 2차 `10_라인배치/라인배치_ENDPART라인배정.xlsx`
- step2에서 RSP→기본품번(10자리) 자동 변환, step5에서 앞10자리 매칭 (컬러 동일단가)
- 미매칭 RSP → GERP 원본금액 그대로 야간금액 적용

### GERP 주야 판정
- 정상 = 전체 생산(주간+야간 포함)
- 추가 = 야간분
- 정산집계 표시: 주간수량 = 정상수량 - 추가수량

### 구ERP
- 비교/검증용 참고 데이터. 최종 정산금액 기준 아님
- LOT B = 야간, 나머지 = 주간
- SUB 라인 + SP3M3: 전 업체 합산 피벗 사용
- SP3M3 구ERP는 모듈품번(MO)으로만 집계 → 라인별 피벗 매칭 불가
- 구ERP 금액 = 구ERP수량 × 기준단가

### 조립품번
- 기준정보 D열 조립품번 우선 (`ANAAS04-01040` 형식)
- GERP col12 조립품번 fallback (`ANAAS0941` 형식)
- 매핑 키: (라인, 품번, 단가) → 조립품번
- 동일품번 다중단가 구분에 활용

### Usage
- Usage=2 품번: 수량 2배 환산 (ANAAS04, HCAMS02 등)

## 대상 라인 10개

| 라인코드 | 라인명 | 유형 | 야간 |
|----------|--------|------|------|
| SD9A01 | 아우터 | OUTER | O |
| SP3M3 | 메인 | MAIN | O |
| WAMAS01 | 웨빙 ASSY | SUB | X |
| WABAS01 | 웨빙 스토퍼 | SUB | X |
| ANAAS04 | 앵커 | SUB | X |
| DRAAS11 | 디링 | SUB | X |
| WASAS01 | 웨빙 스토퍼2 | SUB | X |
| HCAMS02 | 홀더 CLR ASSY | SUB | X |
| HASMS02 | 홀더센스 ASSY | SUB | X |
| ISAMS03 | 이너센스 ASSY | SUB | X |

## 월 마감 절차
1. 실적 파일 2개 수령 (GERP, 구ERP) → 04_실적데이터에 저장
2. `_pipeline_config.py` 수정 (MONTH, 파일 경로)
3. `python run_settlement_pipeline.py` 실행
4. 정산결과_{월}월.xlsx 확인
5. 차이 원인 확인 → STATUS.md 업데이트

## 주의사항
- Python 3.12+, `PYTHONUTF8=1` 필수
- openpyxl, pandas 필요
- 기준정보 파일 수정 시 data_only=False로 열어 수식 보존
- 원본 파일 직접 수정 금지 — 파이프라인이 별도 출력 파일 생성
