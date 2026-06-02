# 2026-06-02 SP3M3 stale output delete

## 결론
- 결과: FAIL / 표준 절차 첫 단계에서 서버 거절.
- 실제 삭제: 0건.
- 실패 위치: `REG_NO=337270` rank DELETE.
- 실패 응답: HTTP 200 / `statusCode=848` / `statusTxt="{0} 가능한 상태가 아닙니다."`

## 대상
| REG_NO | PROD_NO | QTY |
|---:|---|---:|
| 337270 | RSP3SC0644 | 125 |
| 337271 | RSP3SC0590 | 125 |

## 사전검증
- ERP: 두 REG_NO 모두 존재, PROD_NO/QTY 일치.
- SmartMES: 54건, 두 REG_NO 모두 존재.
- SmartMES 매핑:
  - `337270` rank 1 / `RSP3SC0644` / 125
  - `337271` rank 2 / `RSP3SC0590` / 125

## 실행
- 비가역 통보 후 30초 대기 완료.
- `REG_NO=337270` rank DELETE 호출:
  - endpoint: `/prdtPlanMng/deleteDoAddnPrdtPlanInstrMngRankDecideNew.do`
  - payload: `{EXT_PLAN_REG_NO:337270, STD_DA:"2026-06-02", PLAN_DA:"2026-06-02", PROD_NO:"RSP3SC0644", LINE_CD:"SP3M3"}`
  - response: `{"statusTxt":"{0} 가능한 상태가 아닙니다.","statusCode":"848"}`
- 사용자 지시대로 즉시 중단.
- multiList DELETE는 호출하지 않음.

## 사후확인
- ERP/SmartMES 재조회 결과 대상 2건 그대로 잔존.
- SmartMES count 54 유지.
- 삭제 0건.

## 산출
- `90_공통기준/스킬/d0-production-plan/delete_stale_output_regs.py`
