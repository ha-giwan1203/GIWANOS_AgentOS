# 조립비 정산 파이프라인 — 입출력 계약서

> 기준: `_pipeline_config.py` 및 `step1~step7` 소스 코드 기반 (2026-03-24)
> 대상 업체: 대원테크 (vendor_cd = `0109`)

---

## 목차

1. [공통 스키마](#1-공통-스키마)
2. [Step 1: 파일검증](#2-step-1-파일검증)
3. [Step 2: GERP 처리](#3-step-2-gerp-처리)
4. [Step 3: 구ERP 처리](#4-step-3-구erp-처리)
5. [Step 4: 기준정보 매칭](#5-step-4-기준정보-매칭)
6. [Step 5: 정산 계산](#6-step-5-정산-계산)
7. [Step 6: 검증](#7-step-6-검증)
8. [Step 7: 보고서 생성](#8-step-7-보고서-생성)
9. [Step 간 의존 관계](#9-step-간-의존-관계)

---

## 1. 공통 스키마

### 1-1. 공통 메타 필드 (모든 캐시 JSON 포함)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `step` | `int` | ✅ | Step 번호 (1~7) |
| `timestamp` | `str` (ISO 8601) | ✅ | 실행 시각. 예: `"2026-03-24T10:30:00.123456"` |

### 1-2. 라인 코드 목록

| 코드 | 명칭 | 유형 | 야간여부 |
|------|------|------|--------|
| `SD9A01` | 아우터 | `OUTER` | ✅ |
| `SP3M3` | 메인 | `MAIN` | ✅ |
| `WAMAS01` | 웨빙 ASSY | `SUB` | ❌ |
| `WABAS01` | 웨빙 스토퍼 | `SUB` | ❌ |
| `ANAAS04` | 앵커 | `SUB` | ❌ |
| `DRAAS11` | 디링 | `SUB` | ❌ |
| `WASAS01` | 웨빙 스토퍼2 | `SUB` | ❌ |
| `HCAMS02` | 홀더 CLR ASSY | `SUB` | ❌ |
| `HASMS02` | 홀더센스 ASSY | `SUB` | ❌ |
| `ISAMS03` | 이너센스 ASSY | `SUB` | ❌ |

### 1-3. 입력 파일 컬럼 인덱스 (0-based, header=None)

**GERP 파일** (sheet 0, 데이터 시작: row 2)

| 인덱스 | 필드명 | 타입 | 허용값 |
|--------|--------|------|--------|
| 2 | `line` | str | LINE_ORDER 10개 코드 |
| 6 | `product_no` | str | 품번 문자열 |
| 10 | `usage` | int | 1 또는 2 |
| 11 | `assy_part` | str | 조립품번 (형식: `ANAAS0941` 등 라인코드+일련번호) |
| 13 | `shift` | str | `"정상"` (주간), `"추가"` (야간) |
| 14 | `qty` | int | ≥ 0 |
| 15 | `unit_price` | float | ≥ 0 |
| 16 | `amount` | float | ≥ 0 |
| 20 | `vendor_cd` | str | `"0109"` 등 |

**구ERP 파일** (Sheet1, 데이터 시작: row 2)

| 인덱스 | 필드명 | 타입 | 허용값 |
|--------|--------|------|--------|
| 2 | `vendor` | str | 업체코드 포함 문자열 |
| 4 | `part_no` | str | 품번 문자열 |
| 5 | `qty` | int | ≥ 0 |
| 7 | `line_code` | str | OLD_ERP_LINE_MAP 키 또는 임의 |
| 10 | `lot_no` | str | 끝자리: `B`=야간, 그 외=주간 |
| 11 | `unit_cost` | float | ≥ 0 |
| 12 | `amount` | float | ≥ 0 |

**기준정보 파일** (라인코드별 시트, 데이터 시작: row 3)

| 인덱스 | 필드명 | 타입 | 허용값 |
|--------|--------|------|--------|
| 0 | `part_no` | str | 품번 |
| 1 | `vendor_cd` | str | `"0109"` 필터 |
| 2 | `line_code` | str | 라인코드 |
| 3 | `assy_part` | str | 모품번 (참고용) |
| 4 | `usage` | int | 1 또는 2 |
| 5 | `price_type` | str | 임의 문자열 |
| 6 | `price` | float | ≥ 0 (0이면 단가 미등록) |
| 7 | `vtype` | str | 차종 코드 등 |

### 1-4. 피벗 구조 공통 타입

```
Pivot = Dict[line_code: str, Dict[part_no: str, qty: int]]
AllPivot = Dict[part_no: str, qty: int]
```

### 1-5. 판정 분류

| 구분 | 의미 | 파이프라인 동작 |
|------|------|--------------|
| `PASS` | 검증 통과 | 계속 진행 |
| `FAIL` | 검증 실패 | Step 1: 경고 출력 후 계속 / Step 6: FAIL 기록 |
| `INFO` | 참고 정보 | 계속 진행 |

> Step 1 `status=FAIL`이어도 스크립트는 `sys.exit(1)` 호출하지 않음 (경고만). 단, `run_settlement_pipeline.py`에서는 exit code로 중단 판정.

---

## 2. Step 1: 파일검증

### 목적
입력 파일 3개(MASTER, GERP, 구ERP)의 존재 여부, 시트 구조, 컬럼 수, 데이터 존재 여부를 사전 검증한다.

### 입력 파일

| 항목 | 경로 변수 | 필수 |
|------|----------|------|
| 기준정보 Excel | `MASTER_FILE` | ✅ |
| GERP 실적 Excel | `GERP_FILE` | ✅ |
| 구ERP 실적 Excel | `OLDERP_FILE` | ✅ |

### 출력 JSON

**경로**: `_cache/step1_validation.json`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `step` | `int` | ✅ | `1` |
| `timestamp` | `str` | ✅ | ISO 8601 |
| `status` | `str` | ✅ | `"OK"` 또는 `"FAIL"` |
| `checks` | `List[CheckItem]` | ✅ | 항목별 결과 목록 |
| `files.master` | `str` | ✅ | MASTER_FILE 경로 |
| `files.gerp` | `str` | ✅ | GERP_FILE 경로 |
| `files.olderp` | `str` | ✅ | OLDERP_FILE 경로 |

**CheckItem 스키마**:

| 필드 | 타입 | 필수 |
|------|------|------|
| `name` | `str` | ✅ |
| `status` | `str` | ✅ — `"PASS"` 또는 `"FAIL"` |
| `detail` | `str` | ✅ (빈 문자열 가능) |

### 검증 항목 (checks 목록)

| No | 항목명 | FAIL 조건 |
|----|--------|---------|
| 1 | 기준정보 파일 존재 | 파일 없음 |
| 2 | GERP 파일 존재 | 파일 없음 |
| 3 | 구ERP 파일 존재 | 파일 없음 |
| 4 | 기준정보 라인 시트 10개 존재 | 10개 라인 코드 중 누락 시트 존재 |
| 5 | 기준정보 각 라인 데이터행 | row 3+ 데이터 없음 (row 0~2는 헤더) |
| 6 | GERP 시트 열기 | 예외 발생 |
| 7 | GERP 컬럼수 최소 21개 | `df.shape[1] < 21` |
| 8 | GERP 데이터행 1건 이상 | `len(df) - 2 <= 0` |
| 9 | GERP 주야구분 값 (정상/추가 포함) | `'정상'`도 `'추가'`도 없음 |
| 10 | GERP 대원테크(0109) 데이터 존재 | vendor_cd=0109 행 없음 |
| 11 | 구ERP Sheet1 존재 | Sheet1 시트 없음 |
| 12 | 구ERP 데이터행 1건 이상 | `len(df) - 2 <= 0` |
| 13 | 구ERP 컬럼수 최소 13개 | `df.shape[1] < 13` |
| 14 | 구ERP LOTNO 끝자리 B/A/S/C 포함 | `{A,B,C,S} ∩ 끝자리값 = ∅` |
| 15 | 구ERP 대원테크(0109) 데이터 존재 | vendor 컬럼에 0109 없음 |

### 실패 조건 (status = "FAIL")
- 위 항목 중 하나라도 FAIL이면 `status = "FAIL"`
- 스크립트 자체는 계속 실행 (sys.exit 없음)
- `run_settlement_pipeline.py`에서 exit code=0이어도 `status=FAIL`이면 중단 처리

### 경고 조건
- 없음 (모두 PASS/FAIL 이진 판정)

### 샘플 JSON (축약)

```json
{
  "step": 1,
  "timestamp": "2026-03-24T10:00:00.000000",
  "status": "OK",
  "checks": [
    {"name": "기준정보 파일 존재", "status": "PASS", "detail": "C:\\...\\기준정보.xlsx"},
    {"name": "GERP 컬럼수 최소 21개", "status": "PASS", "detail": "실제 24열"},
    {"name": "기준정보 [SD9A01] 데이터행", "status": "PASS", "detail": "15행"}
  ],
  "files": {
    "master": "C:\\...\\기준정보.xlsx",
    "gerp": "C:\\...\\GERP_실적현황.xlsx",
    "olderp": "C:\\...\\구ERP_실적현황.xlsx"
  }
}
```

### 다음 Step 전달 항목
- 직접 전달 없음. Step 2, 3, 4는 원본 파일을 직접 읽음.

---

## 3. Step 2: GERP 처리

### 목적
GERP 파일에서 대원테크(0109) 데이터 필터 → 주야 분리 → 라인별 품번-수량 피벗 생성.

### 입력

| 항목 | 경로 변수 | 필수 |
|------|----------|------|
| GERP 실적 Excel | `GERP_FILE` | ✅ |

### 출력 JSON

**경로**: `_cache/step2_gerp.json`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `step` | `int` | ✅ | `2` |
| `timestamp` | `str` | ✅ | ISO 8601 |
| `total_rows` | `int` | ✅ | 대원테크 행 수 |
| `day_pivot` | `Pivot` | ✅ | 주간: `{line: {part_no: qty}}` |
| `night_pivot` | `Pivot` | ✅ | 야간: `{line: {part_no: qty}}` |
| `unmatched_lines` | `List[str]` | ✅ | GERP 데이터 없는 라인 코드 목록 |
| `all_gerp_lines` | `List[str]` | ✅ | 전체(전 업체) GERP 라인 코드 목록 |

### 필드 제약조건

- `day_pivot`, `night_pivot` 키: LINE_ORDER 10개 중 실적 있는 것만 포함 (없으면 키 자체 없음)
- qty 값: `int`, ≥ 0
- `shift='정상'` → `shift_type='주간'`, `shift='추가'` → `shift_type='야간'`, 그 외 → `'주간'` 처리

### 실패 조건
- `GERP_FILE` 파일 없음 → `sys.exit(1)`

### 경고 조건
- `unmatched_lines` 비어있지 않음 → 콘솔 경고 출력 (실행 계속)

### 샘플 JSON (축약)

```json
{
  "step": 2,
  "timestamp": "2026-03-24T10:01:00.000000",
  "total_rows": 3420,
  "day_pivot": {
    "SD9A01": {"AB1234": 500, "AB5678": 320},
    "SP3M3":  {"SP0001": 1200}
  },
  "night_pivot": {
    "SD9A01": {"AB1234": 80}
  },
  "unmatched_lines": ["WASAS01"],
  "all_gerp_lines": ["SD9A01", "SP3M3", "WAMAS01", "..."]
}
```

### 다음 Step 전달 항목

| 필드 | 사용처 |
|------|--------|
| `day_pivot` | Step 4 (GERP 전체 품번 추출), Step 5 (계산) |
| `night_pivot` | Step 4 (GERP 전체 품번 추출), Step 5 (계산) |

---

## 4. Step 3: 구ERP 처리

### 목적
구ERP 파일 로드 → LOT NO 끝자리로 주야 판정 → 품번-수량 피벗 2종 생성
(OUTER/MAIN: 라인별, SUB: 전 업체 합산).

### 입력

| 항목 | 경로 변수 | 필수 |
|------|----------|------|
| 구ERP 실적 Excel | `OLDERP_FILE` | ✅ |

### 출력 JSON

**경로**: `_cache/step3_olderp.json`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `step` | `int` | ✅ | `3` |
| `timestamp` | `str` | ✅ | ISO 8601 |
| `total_rows_all` | `int` | ✅ | 전 업체 전체 행 수 |
| `total_rows_0109` | `int` | ✅ | 대원테크 행 수 |
| `line_day_pivot` | `Pivot` | ✅ | 대원테크 라인별 주간 피벗 (SD9A01, SP3M3만) |
| `line_night_pivot` | `Pivot` | ✅ | 대원테크 라인별 야간 피벗 (SD9A01, SP3M3만) |
| `all_day_pivot` | `AllPivot` | ✅ | 전 업체 주간 피벗 (SUB 라인 매칭용) |
| `all_night_pivot` | `AllPivot` | ✅ | 전 업체 야간 피벗 (SUB 라인 매칭용) |
| `all_total_pivot` | `AllPivot` | ✅ | 전 업체 주야 합산 피벗 |

### 필드 제약조건

- 주야 판정: `lot_no.endswith('B')` → 야간, 그 외 → 주간
- `line_day_pivot`, `line_night_pivot`: 키는 `SD9A01`, `SP3M3`만 (데이터 없으면 해당 키 없음)
- qty 값: `int`, ≥ 0
- `OLD_ERP_LINE_MAP` 매핑: `TD9→SD9A01`, `D9N6→SD9A01`, `SP3S03→SP3M3`

### 실패 조건
- `OLDERP_FILE` 파일 없음 → `sys.exit(1)`

### 경고 조건
- 없음

### 샘플 JSON (축약)

```json
{
  "step": 3,
  "timestamp": "2026-03-24T10:02:00.000000",
  "total_rows_all": 15000,
  "total_rows_0109": 820,
  "line_day_pivot": {
    "SD9A01": {"AB1234": 490},
    "SP3M3":  {"SP0001": 1180}
  },
  "line_night_pivot": {
    "SD9A01": {"AB1234": 75}
  },
  "all_day_pivot":   {"AB1234": 490, "WM0001": 2000, "...": 0},
  "all_night_pivot": {"AB1234": 75},
  "all_total_pivot": {"AB1234": 565, "WM0001": 2000}
}
```

### 다음 Step 전달 항목

| 필드 | 사용처 |
|------|--------|
| `line_day_pivot` | Step 5 (SD9A01, SP3M3 구ERP 수량) |
| `line_night_pivot` | Step 5 (SD9A01, SP3M3 구ERP 야간 수량) |
| `all_day_pivot` | Step 5 (SUB 라인 구ERP 수량) |
| `all_night_pivot` | Step 5 (SUB 라인 구ERP 야간 수량) |
| `all_total_pivot` | Step 5 (참조용) |

---

## 5. Step 4: 기준정보 매칭

### 목적
기준정보 파일에서 라인별 품번/단가/Usage 로딩 → GERP 품번과 대조 → 미등록 품번 추출.

### 입력

| 항목 | 경로 변수 | 필수 |
|------|----------|------|
| 기준정보 Excel | `MASTER_FILE` | ✅ |
| `_cache/step2_gerp.json` | `CACHE_STEP2` | ✅ |

### 출력 JSON

**경로**: `_cache/step4_matched.json`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `step` | `int` | ✅ | `4` |
| `timestamp` | `str` | ✅ | ISO 8601 |
| `master` | `Dict[str, List[MasterItem]]` | ✅ | 라인별 기준정보 행 목록 |
| `master_pn_count` | `int` | ✅ | 기준정보 전체 품번 수 |
| `gerp_pn_count` | `int` | ✅ | GERP 전체 품번 수 |
| `unmatched_gerp` | `List[str]` | ✅ | 기준정보 없는 GERP 품번 목록 (정렬) |
| `rsp_map` | `Dict[str, str]` | ✅ | RSP품번 → 완성품 품번 역추적 맵 |

**MasterItem 스키마**:

| 필드 | 타입 | 필수 | 허용값/제약 |
|------|------|------|-----------|
| `part_no` | `str` | ✅ | 비어있지 않음 |
| `price` | `float` | ✅ | ≥ 0.0 (0.0이면 단가 미등록) |
| `usage` | `int` | ✅ | `1` 또는 `2` |
| `price_type` | `str` | ✅ | 빈 문자열 허용 |
| `vtype` | `str` | ✅ | 빈 문자열 허용 |

### 필드 제약조건

- `master` 키: LINE_ORDER 10개 (시트 없으면 빈 리스트 `[]`)
- `vendor_cd != '0109'`인 행은 필터 제외
- `rsp_map` 키: `RSP`로 시작하는 품번만 포함
- `unmatched_gerp`: `{'nan', 'None', ''}` 제외 후 정렬

### 실패 조건
- `CACHE_STEP2` 없음 → `sys.exit(1)`
- `MASTER_FILE` 없음 → `sys.exit(1)`

### 경고 조건 (INFO)
- `unmatched_gerp` 비어있지 않음 → 콘솔 출력 (실행 계속)

### 샘플 JSON (축약)

```json
{
  "step": 4,
  "timestamp": "2026-03-24T10:03:00.000000",
  "master": {
    "SD9A01": [
      {"part_no": "AB1234", "price": 350.0, "usage": 1, "price_type": "기준", "vtype": "SD9"},
      {"part_no": "AB5678", "price": 620.0, "usage": 1, "price_type": "기준", "vtype": "SD9"}
    ],
    "SP3M3": [
      {"part_no": "SP0001", "price": 120.0, "usage": 1, "price_type": "기준", "vtype": "SP3"}
    ],
    "WAMAS01": [],
    "WABAS01": [
      {"part_no": "WB0001", "price": 0.0, "usage": 1, "price_type": "", "vtype": ""}
    ]
  },
  "master_pn_count": 85,
  "gerp_pn_count": 88,
  "unmatched_gerp": ["XX-UNKNOWN-01", "XX-UNKNOWN-02"],
  "rsp_map": {"RSP00123": "SP0001"}
}
```

### 다음 Step 전달 항목

| 필드 | 사용처 |
|------|--------|
| `master` | Step 5 (라인별 품번 루프, 단가/Usage 조회) |
| `unmatched_gerp` | Step 5 → Step 6 (미매핑 검증), Step 7 (02_미매핑품번 시트) |

---

## 6. Step 5: 정산 계산

### 목적
라인별 품번별 GERP/구ERP 수량 × 단가 계산 → 야간 가산 적용 → 합계 집계.

### 입력

| 항목 | 경로 변수 | 필수 |
|------|----------|------|
| `_cache/step2_gerp.json` | `CACHE_STEP2` | ✅ |
| `_cache/step3_olderp.json` | `CACHE_STEP3` | ✅ |
| `_cache/step4_matched.json` | `CACHE_STEP4` | ✅ |

### 출력 JSON

**경로**: `_cache/step5_settlement.json`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `step` | `int` | ✅ | `5` |
| `timestamp` | `str` | ✅ | ISO 8601 |
| `month` | `str` | ✅ | 대상 월 (예: `"03"`) |
| `lines` | `Dict[str, LineResult]` | ✅ | 라인별 계산 결과 |
| `summary` | `List[SummaryRow]` | ✅ | 라인별 요약 10행 |
| `grand_gerp_amt` | `int` | ✅ | 전체 GERP 합계 금액 |
| `grand_erp_amt` | `int` | ✅ | 전체 구ERP 합계 금액 |
| `grand_diff_amt` | `int` | ✅ | 전체 차이 금액 |
| `unmatched_gerp` | `List[str]` | ✅ | Step 4에서 전달받은 미매핑 품번 목록 |

**LineResult 스키마**:

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `items` | `List[LineItem]` | ✅ | 품번별 상세 |
| `total_gerp_day_qty` | `int` | ✅ | GERP 주간 수량 합계 |
| `total_gerp_day_amt` | `int` | ✅ | GERP 주간 금액 합계 |
| `total_gerp_ngt_qty` | `int` | ✅ | GERP 야간 수량 합계 |
| `total_gerp_ngt_amt` | `int` | ✅ | GERP 야간 금액 합계 |
| `total_gerp_amt` | `int` | ✅ | GERP 합계 금액 (주간+야간) |
| `total_erp_day_qty` | `int` | ✅ | 구ERP 주간 수량 합계 |
| `total_erp_day_amt` | `int` | ✅ | 구ERP 주간 금액 합계 |
| `total_erp_ngt_qty` | `int` | ✅ | 구ERP 야간 수량 합계 |
| `total_erp_ngt_amt` | `int` | ✅ | 구ERP 야간 금액 합계 |
| `total_erp_amt` | `int` | ✅ | 구ERP 합계 금액 (주간+야간) |
| `diff_amt` | `int` | ✅ | GERP - 구ERP 차이 |

**LineItem 스키마**:

| 필드 | 타입 | 필수 | 허용값/제약 |
|------|------|------|-----------|
| `part_no` | `str` | ✅ | 품번 |
| `assy_part` | `str` | ✅ | 조립품번 (기준정보 col3 우선, 없으면 GERP col11 fallback, 빈 문자열 허용) |
| `price` | `float` | ✅ | 기준정보 단가 ≥ 0 |
| `usage` | `int` | ✅ | 1 또는 2 |
| `price_type` | `str` | ✅ | 빈 문자열 허용 |
| `vtype` | `str` | ✅ | 빈 문자열 허용 |
| `gerp_day_qty` | `int` | ✅ | GERP 주간 수량 (usage 환산 후) |
| `gerp_day_amt` | `int` | ✅ | `round(gerp_day_qty × price)` |
| `gerp_ngt_qty` | `int` | ✅ | GERP 야간 수량 (has_night=False 라인은 0) |
| `gerp_ngt_amt` | `int` | ✅ | 야간 금액 (라인별 계산식 적용) |
| `gerp_total_amt` | `int` | ✅ | `gerp_day_amt + gerp_ngt_amt` |
| `gerp_orig_day_amt` | `int` | ✅ | GERP 원본 주간금액 (GERP 파일 amount 컬럼 합산, 다중단가 비교용) |
| `gerp_orig_ngt_amt` | `int` | ✅ | GERP 원본 야간금액 (GERP 파일 amount 컬럼 합산) |
| `erp_day_qty` | `int` | ✅ | 구ERP 주간 수량 (usage 환산 후) |
| `erp_day_amt` | `int` | ✅ | `round(erp_day_qty × price)` |
| `erp_ngt_qty` | `int` | ✅ | 구ERP 야간 수량 (has_night=False는 0) |
| `erp_ngt_amt` | `int` | ✅ | 구ERP 야간 금액 |
| `erp_tot_qty` | `int` | ✅ | 구ERP 주+야 합산 총수량 (원본합산 검증용) |
| `price_judgment` | `str \| null` | ✅ | SD9A01만: `"야간가산"`, `"기본"`, `null` |

**SummaryRow 스키마**:

| 필드 | 타입 | 필수 |
|------|------|------|
| `line` | `str` | ✅ |
| `name` | `str` | ✅ |
| `gerp_amt` | `int` | ✅ |
| `erp_amt` | `int` | ✅ |
| `diff_amt` | `int` | ✅ |

### 야간 금액 계산식

| 라인 | 조건 | 계산식 |
|------|------|--------|
| `SP3M3` | 야간qty > 0 | `야간qty × 170` (고정단가) |
| `SD9A01` | 야간qty > 0, price ≤ 500 | `round(야간qty × price × 1.3)` (야간가산) |
| `SD9A01` | 야간qty > 0, price > 500 | `round(야간qty × price)` (기본) |
| 기타 (SUB) | — | `0` (has_night = False) |

### SD9A01 단가기준판정

| 조건 | price_judgment 값 |
|------|-----------------|
| `lc != 'SD9A01'` | `null` |
| `gerp_ngt_qty == 0` | `null` |
| `price ≤ 500` | `"야간가산"` |
| `price > 500` | `"기본"` |

### 실패 조건
- CACHE_STEP2, CACHE_STEP3, CACHE_STEP4 중 하나라도 없음 → `sys.exit(1)`

### 경고 조건
- 없음 (계산 결과 이상은 Step 6에서 검증)

### 샘플 JSON (축약)

```json
{
  "step": 5,
  "timestamp": "2026-03-24T10:04:00.000000",
  "month": "03",
  "lines": {
    "SD9A01": {
      "items": [
        {
          "part_no": "AB1234", "price": 350.0, "usage": 1,
          "price_type": "기준", "vtype": "SD9",
          "gerp_day_qty": 500, "gerp_day_amt": 175000,
          "gerp_ngt_qty": 80,  "gerp_ngt_amt": 36400,
          "gerp_total_amt": 211400,
          "erp_day_qty": 490, "erp_day_amt": 171500,
          "erp_ngt_qty": 75,  "erp_ngt_amt": 34125,
          "price_judgment": "야간가산"
        }
      ],
      "total_gerp_day_qty": 820, "total_gerp_day_amt": 346200,
      "total_gerp_ngt_qty": 80,  "total_gerp_ngt_amt": 36400,
      "total_gerp_amt": 382600,
      "total_erp_day_qty": 805, "total_erp_day_amt": 340525,
      "total_erp_ngt_qty": 75,  "total_erp_ngt_amt": 34125,
      "total_erp_amt": 374650,
      "diff_amt": 7950
    }
  },
  "summary": [
    {"line": "SD9A01", "name": "아우터", "gerp_amt": 382600, "erp_amt": 374650, "diff_amt": 7950}
  ],
  "grand_gerp_amt": 1250000,
  "grand_erp_amt":  1242050,
  "grand_diff_amt": 7950,
  "unmatched_gerp": ["XX-UNKNOWN-01"]
}
```

### 다음 Step 전달 항목

| 필드 | 사용처 |
|------|--------|
| `lines` | Step 6 (검증), Step 7 (라인별 시트) |
| `summary` | Step 6 (차이 확인), Step 7 (00_정산집계) |
| `grand_gerp_amt`, `grand_erp_amt`, `grand_diff_amt` | Step 6 (합계 일관성), Step 7 (합계행) |
| `unmatched_gerp` | Step 6 (미매핑 검증), Step 7 (02_미매핑품번 시트) |

---

## 7. Step 6: 검증

### 목적
Step 5 계산 결과의 내부 일관성 및 비즈니스 규칙 준수 여부를 7개 항목으로 자동 검증.

### 입력

| 항목 | 경로 변수 | 필수 |
|------|----------|------|
| `_cache/step5_settlement.json` | `CACHE_STEP5` | ✅ |

### 출력 JSON

**경로**: `_cache/step6_validation.json`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `step` | `int` | ✅ | `6` |
| `timestamp` | `str` | ✅ | ISO 8601 |
| `overall` | `str` | ✅ | `"PASS"` 또는 `"FAIL"` |
| `pass` | `int` | ✅ | PASS 항목 수 |
| `fail` | `int` | ✅ | FAIL 항목 수 |
| `info` | `int` | ✅ | INFO 항목 수 |
| `checks` | `List[CheckItem6]` | ✅ | 7개 항목 결과 |

**CheckItem6 스키마**:

| 필드 | 타입 | 필수 |
|------|------|------|
| `no` | `int` | ✅ |
| `name` | `str` | ✅ |
| `status` | `str` | ✅ — `"PASS"`, `"FAIL"`, `"INFO"` |
| `detail` | `str` | ✅ |

### 검증 항목 7개

| No | 항목명 | 판정 | FAIL/INFO 조건 |
|----|--------|------|--------------|
| 1 | 전체합계 일관성 (라인합산 == grand) | PASS/FAIL | 라인 합산 ≠ grand 값 |
| 2 | SD9A01 단가기준판정 규칙 | PASS/FAIL | 야간실적 없는 행에 판정값 있음 / 단가 기준 불일치 |
| 3 | WABAS01 단가=0 품번 현황 | INFO (항상) | 단가=0 건수 및 실적 유무 보고 |
| 4 | Usage=2 품번 수량 짝수 여부 | PASS/INFO | Usage=2 품번에 홀수 수량 존재 (비정상 가능) |
| 5 | SP3M3 야간 고정단가 170원 적용 | PASS/FAIL | `gerp_ngt_amt ≠ gerp_ngt_qty × 170` |
| 6 | GERP 미매핑 품번 현황 | PASS/INFO | `unmatched_gerp` 비어있지 않음 |
| 7 | GERP vs 구ERP 라인별 차이 | PASS/INFO | `diff_amt ≠ 0`인 라인 존재 |

### 실패 조건
- `CACHE_STEP5` 없음 → `sys.exit(1)`
- `overall = "FAIL"`: 항목 1, 2, 5 중 하나라도 FAIL

### 경고 조건 (INFO)
- 항목 3, 6, 7: 항상 또는 조건부 INFO (실행 중단 없음)
- FAIL 항목 있을 시 콘솔에 STATUS.md 기록 권장 메시지 출력

### 샘플 JSON (축약)

```json
{
  "step": 6,
  "timestamp": "2026-03-24T10:05:00.000000",
  "overall": "PASS",
  "pass": 4,
  "fail": 0,
  "info": 3,
  "checks": [
    {"no": 1, "name": "전체합계 일관성 (라인합산 == grand)", "status": "PASS", "detail": "GERP: 1250000 vs 1250000  구ERP: 1242050 vs 1242050"},
    {"no": 3, "name": "WABAS01 단가=0 품번 현황", "status": "INFO", "detail": "단가=0: 2건  (실적있음: 1건) → 단가 확인 필요"},
    {"no": 7, "name": "GERP vs 구ERP 라인별 차이", "status": "INFO", "detail": "SD9A01:+7950; SP3M3:+1200"}
  ]
}
```

### 다음 Step 전달 항목
- 없음. Step 7은 Step 5 JSON을 직접 사용.

---

## 8. Step 7: 보고서 생성

### 목적
Step 5 JSON → 최종 xlsx 보고서 생성 (4종 시트 구성).

### 입력

| 항목 | 경로 변수 | 필수 |
|------|----------|------|
| `_cache/step5_settlement.json` | `CACHE_STEP5` | ✅ |

### 출력 파일

**경로**: `OUTPUT_FILE` (예: `05_생산실적\조립비정산/정산결과_03월.xlsx`)

**시트 구성**:

| 시트명 | 내용 |
|--------|------|
| `00_정산집계` | 라인별 GERP/구ERP 수량·금액·차이 요약표 |
| `SD9A01` ~ `ISAMS03` | 라인별 품번 상세 (10개 시트) |
| `01_차이분석` | 차이 발생 품번만 추출 |
| `02_미매핑품번` | 기준정보 없는 GERP 품번 |

**00_정산집계 컬럼 (row 3 헤더)**:

```
라인코드 | 라인명 | 유형 | GERP_주간수량 | GERP_야간수량 | GERP_주간금액 | GERP_야간금액 | GERP_합계금액
| 구ERP_주간수량 | 구ERP_야간수량 | 구ERP_주간금액 | 구ERP_야간금액 | 구ERP_합계금액
| 차이금액(GERP-구ERP)
```

**라인별 시트 헤더 (has_night=True, SD9A01)**:

```
No | 품번 | 차종 | Usage | 단가 | 단가유형
| GERP주간수량 | GERP주간금액 | GERP야간수량 | GERP야간금액(최종) | GERP합계금액
| 구ERP주간수량 | 구ERP주간금액 | 구ERP야간수량 | 구ERP야간금액 | 구ERP합계금액
| 차이금액 | 단가기준판정
```

**라인별 시트 헤더 (has_night=True, SP3M3)**:

```
No | 품번 | 차종 | Usage | 단가 | 단가유형
| GERP주간수량 | GERP주간금액 | GERP야간수량 | GERP야간금액(170원)
| 구ERP주간수량 | 구ERP주간금액 | 구ERP야간수량 | 구ERP야간금액 | 구ERP합계금액
| 차이금액
```

**라인별 시트 헤더 (has_night=False, SUB 8개)**:

```
No | 품번 | 차종 | Usage | 단가 | 단가유형
| GERP수량 | GERP금액 | 구ERP수량 | 구ERP금액 | 차이금액
```

**스타일 규칙**:

| 요소 | 적용 |
|------|------|
| 헤더 배경 | 진청 `#1B2A4A`, 흰 글씨 |
| 차이 음수 | 빨강 `#FCE4EC` |
| 차이 양수 | 초록 `#E8F5E9` |
| 합계행 | 회색 `#F5F5F5`, 굵게 |
| 숫자 포맷 | `#,##0` (천단위 쉼표) |
| 미매핑 품번 | 노랑 `#FFF2CC` |

### 실패 조건
- `CACHE_STEP5` 없음 → `sys.exit(1)`
- `OUTPUT_FILE` 저장 실패 (디스크 용량 부족, 파일 잠금 등) → 예외 발생

### 경고 조건
- 없음

### 다음 Step 전달 항목
- 없음. 최종 출력.

---

## 9. Step 간 의존 관계

```
입력 파일 (xlsx)
│
├─ Step 1: 파일검증  ──────────────────────── 독립 (파일 존재/구조만 확인)
│
├─ Step 2: GERP 처리  ────────────────────── 독립
│   └─ step2_gerp.json
│       ├─ Step 4: 기준정보 매칭
│       │   └─ step4_matched.json
│       │       └─ Step 5: 정산 계산
│       │           └─ step5_settlement.json
│       │               ├─ Step 6: 검증
│       │               └─ Step 7: 보고서 → 정산결과_XX월.xlsx
│       └─ (Step 5에서 직접 사용)
│
└─ Step 3: 구ERP 처리  ───────────────────── 독립
    └─ step3_olderp.json
        └─ Step 5: 정산 계산 (step2, step4와 함께 사용)
```

**병렬 실행 가능**: Step 2, Step 3은 상호 독립
**순차 필수**: Step 4 → Step 5 → Step 6, 7
**Step 4 선행 필요**: Step 2 완료 후 Step 4 실행 가능

### 캐시 파일 매핑

| Step | 출력 캐시 파일 | 다음 Step 의존 |
|------|-------------|--------------|
| 1 | `_cache/step1_validation.json` | — |
| 2 | `_cache/step2_gerp.json` | Step 4, 5 |
| 3 | `_cache/step3_olderp.json` | Step 5 |
| 4 | `_cache/step4_matched.json` | Step 5 |
| 5 | `_cache/step5_settlement.json` | Step 6, 7 |
| 6 | `_cache/step6_validation.json` | — |
| 7 | `OUTPUT_FILE` (xlsx) | — |
