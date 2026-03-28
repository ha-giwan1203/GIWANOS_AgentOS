# 품번조회 MCP 기획

> 상태: 기획 단계 (미구현)
> 작성일: 2026-03-24

---

## 목적

기준정보 파일에서 품번·단가·Usage·라인 정보를 API로 조회.
정산 계산, 라인배치 검증, 단가 확인 등에서 공통으로 사용한다.

---

## 입력 / 출력

### 공통 입력
```json
{
  "master_file": "절대경로 (생략 시 기본값 사용)"
}
```
기본값: `C:\Users\User\Desktop\업무리스트\05_생산실적\조립비정산\01_기준정보\기준정보_라인별정리_최종_V1_20260316.xlsx`

### 공통 출력 (오류 시)
```json
{
  "error": "오류 메시지",
  "code": "PART_NOT_FOUND | FILE_NOT_FOUND | VENDOR_MISMATCH"
}
```

---

## 엔드포인트 정의

### GET /part/{part_no}
단일 품번 조회

**요청** `GET /part/12345-67890`

**응답**
```json
{
  "part_no": "12345-67890",
  "vendor_code": "0109",
  "line": "SD9A01",
  "line_name": "아우터",
  "price": 380,
  "price_type": "야간가산",
  "usage": 1,
  "vtype": "세단",
  "found": true
}
```

품번 없을 경우:
```json
{
  "part_no": "99999-00000",
  "found": false,
  "error": "기준정보에 등록되지 않은 품번"
}
```

---

### POST /part/batch
다수 품번 일괄 조회

**요청**
```json
{
  "part_nos": ["12345-67890", "22222-33333", "99999-00000"]
}
```

**응답**
```json
{
  "results": [
    {"part_no": "12345-67890", "found": true, "price": 380, "line": "SD9A01", "usage": 1},
    {"part_no": "22222-33333", "found": true, "price": 170, "line": "SP3M3",  "usage": 1},
    {"part_no": "99999-00000", "found": false}
  ],
  "found_count": 2,
  "not_found_count": 1,
  "not_found": ["99999-00000"]
}
```

---

### GET /line/{line_code}
라인 전체 품번 목록 조회

**요청** `GET /line/SD9A01`

**응답**
```json
{
  "line": "SD9A01",
  "line_name": "아우터",
  "vendor_code": "0109",
  "total_count": 45,
  "priced_count": 43,
  "zero_price_count": 2,
  "items": [
    {"part_no": "12345-67890", "price": 380, "usage": 1, "price_type": "야간가산"},
    {"part_no": "22222-11111", "price": 0,   "usage": 1, "price_type": ""}
  ]
}
```

---

### GET /rsp/{rsp_part_no}
RSP 모듈품번 → 완성품 품번 역추적

**요청** `GET /rsp/RSP-12345`

**응답**
```json
{
  "rsp_part_no": "RSP-12345",
  "mapped_part_no": "12345-67890",
  "found": true
}
```

---

### GET /lines
전체 라인 요약 조회

**응답**
```json
{
  "lines": [
    {"code": "SD9A01", "name": "아우터",        "type": "OUTER", "part_count": 45, "has_night": true},
    {"code": "SP3M3",  "name": "메인",          "type": "MAIN",  "part_count": 30, "has_night": true},
    {"code": "WAMAS01","name": "웨빙 ASSY",     "type": "SUB",   "part_count": 12, "has_night": false}
  ],
  "total_parts": 180,
  "vendor_code": "0109",
  "master_file": "기준정보_라인별정리_최종_V1_20260316.xlsx",
  "loaded_at": "2026-03-24T09:00:00"
}
```

---

## 기술 스택 (구현 시 참고)

| 항목 | 내용 |
|------|------|
| 런타임 | Python 3.12 |
| 프레임워크 | FastAPI |
| 엑셀 파싱 | pandas + openpyxl |
| 캐싱 | 파일 mtime 기반 인메모리 캐시 (파일 변경 시 자동 갱신) |
| 포트 | 8702 (임시) |
| 인증 | 로컬 전용 → 없음 |
| 기반 로직 | `step4_기준정보매칭.py` `load_master()` 함수 |

---

## 캐싱 전략

기준정보 파일은 월 단위로 교체되므로, 파일 mtime을 감시해 변경 시 자동 리로드.

```
파일 요청 → mtime 비교 → 변경 없으면 캐시 반환 → 변경 있으면 리로드 후 캐시 갱신
```

---

## Claude Tool Use 연동 예시

```json
{
  "name": "lookup_part_price",
  "description": "기준정보에서 품번의 단가·Usage·라인 정보를 조회한다.",
  "input_schema": {
    "type": "object",
    "properties": {
      "part_no": {
        "type": "string",
        "description": "조회할 품번 (예: 12345-67890)"
      }
    },
    "required": ["part_no"]
  }
},
{
  "name": "lookup_parts_batch",
  "description": "다수 품번을 일괄 조회한다. 미등록 품번 목록도 함께 반환.",
  "input_schema": {
    "type": "object",
    "properties": {
      "part_nos": {
        "type": "array",
        "items": {"type": "string"},
        "description": "조회할 품번 목록"
      }
    },
    "required": ["part_nos"]
  }
}
```

---

## 구현 우선순위

1. `GET /part/{part_no}` + `POST /part/batch` — 정산 계산에서 즉시 활용
2. `GET /line/{line_code}` — 라인 전체 단가 확인용
3. `GET /rsp/{rsp_part_no}` — 모듈품번 역추적
4. `GET /lines` — 대시보드 연동 시
