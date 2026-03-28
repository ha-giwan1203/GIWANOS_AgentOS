# 정산검증 MCP 기획

> 상태: 기획 단계 (미구현)
> 작성일: 2026-03-24

---

## 목적

정산 결과 파일의 자동 검증을 API 엔드포인트로 노출.
Claude나 외부 도구가 정산 파일 경로만 넘기면 7개 항목 검증 결과를 JSON으로 반환한다.

---

## 입력 / 출력

### 공통 입력 (모든 엔드포인트)
```json
{
  "settlement_file": "절대경로 또는 상대경로 (xlsx)",
  "month": "02"
}
```

### 공통 출력 (오류 시)
```json
{
  "error": "오류 메시지",
  "code": "FILE_NOT_FOUND | SHEET_MISSING | PARSE_ERROR"
}
```

---

## 엔드포인트 정의

### POST /validate
정산 결과 파일 전체 검증 (7개 항목)

**요청**
```json
{
  "settlement_file": "C:/Users/User/Desktop/업무리스트/05_생산실적\조립비정산/정산결과_02월.xlsx",
  "month": "02"
}
```

**응답**
```json
{
  "overall": "PASS | FAIL",
  "summary": {
    "pass": 5,
    "fail": 1,
    "info": 1
  },
  "checks": [
    {
      "no": 1,
      "name": "전체합계 일관성",
      "status": "PASS",
      "detail": "GERP: 1,234,567  구ERP: 1,189,000"
    },
    {
      "no": 2,
      "name": "SD9A01 단가기준판정",
      "status": "FAIL",
      "detail": "오류: ['12345-67890(단가=300,판정=기본,기대=야간가산)']"
    }
  ],
  "timestamp": "2026-03-24T10:00:00"
}
```

---

### POST /validate/item
단일 항목 검증 (빠른 점검용)

**요청**
```json
{
  "settlement_file": "...",
  "check_no": 2
}
```
`check_no`: 1~7 (1=합계, 2=SD9A01, 3=WABAS01, 4=Usage, 5=SP3M3, 6=미매핑, 7=차이)

**응답**
```json
{
  "no": 2,
  "name": "SD9A01 단가기준판정",
  "status": "PASS",
  "detail": "전체 정상"
}
```

---

### GET /schema
검증 항목 스키마 조회 (항목번호·이름·판정기준 목록)

**응답**
```json
{
  "checks": [
    {"no": 1, "name": "전체합계 일관성",      "criteria": "라인합산 == grand 합계"},
    {"no": 2, "name": "SD9A01 단가기준판정",  "criteria": "단가≤500→야간가산, >500→기본"},
    {"no": 3, "name": "WABAS01 단가=0 현황",  "criteria": "INFO (건수 및 실적 유무)"},
    {"no": 4, "name": "Usage=2 수량환산",      "criteria": "2배 환산 품번 수량 짝수 여부"},
    {"no": 5, "name": "SP3M3 야간 고정단가",   "criteria": "야간qty×170원 일치"},
    {"no": 6, "name": "미매핑 품번",           "criteria": "INFO (건수)"},
    {"no": 7, "name": "GERP vs 구ERP 차이",    "criteria": "INFO (라인별 차이금액)"}
  ]
}
```

---

## 기술 스택 (구현 시 참고)

| 항목 | 내용 |
|------|------|
| 런타임 | Python 3.12 |
| 프레임워크 | FastAPI (또는 Flask) |
| 엑셀 파싱 | openpyxl (data_only=True) |
| 포트 | 8701 (임시) |
| 인증 | 로컬 전용 → 없음 (추후 API Key 추가) |
| 기반 스크립트 | `step6_검증.py`, `검증_정산결과.py` |

---

## 구현 우선순위

1. `POST /validate` — 핵심 기능, 최우선
2. `GET /schema` — Claude Tool Use 연동 시 필요
3. `POST /validate/item` — 필요 시 추가

---

## Claude Tool Use 연동 예시

```json
{
  "name": "validate_settlement",
  "description": "정산 결과 파일 자동 검증. PASS/FAIL/INFO 7개 항목 반환.",
  "input_schema": {
    "type": "object",
    "properties": {
      "settlement_file": {"type": "string", "description": "정산 결과 xlsx 절대경로"},
      "month": {"type": "string", "description": "정산 대상 월 (예: 02)"}
    },
    "required": ["settlement_file"]
  }
}
```
