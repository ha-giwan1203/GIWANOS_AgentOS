# RETRACTOR WAMAS01 누락 추출 검토 기록

- 작업일: 2026-05-27
- 입력 A: `C:\Users\User\Downloads\조립비 현황관리(New)(제품번호).xlsx`
- 입력 B: `05_생산실적\조립비정산\조립비 현황관리 전체 데이터_260519.xlsx` / `SQL Results`
- 산출: `05_생산실적\조립비정산\05월\retractor_wamas01_missing_20260527.xlsx` (2026-05-27 99_임시수집에서 이관, 정산 작업폴더 관행)

## 기준

- A는 원본을 수정하지 않고, 내부 XML의 숫자형 공백 셀만 메모리상 정리해 읽음.
- A 필터: `상태=확정`, `제품군=RETRACTOR`.
- B 비교: `PROD_NO`별 `DECIDE_CD=Y` 행의 `ASSY_LINE_CD` 집합에 `WAMAS01`이 없는지 확인.
- B에는 맨 앞 빈 번호 컬럼이 있어 위치 숫자 대신 헤더명 기준으로 컬럼을 매핑함.

## 결과

| 항목 | 건수 |
|---|---:|
| A RETRACTOR 전체 PROD_NO 행 | 3,860 |
| A RETRACTOR 확정 행 | 3,858 |
| A RETRACTOR 확정 고유 PROD_NO | 3,858 |
| WAMAS01 미보유 PROD_NO | 385 |
| 전체데이터에 PROD_NO 자체가 없는 건 | 0 |
| B 전체 데이터 행 | 51,309 |

## 검증

- 결과 파일 재오픈 확인: PASS.
- 시트 구성 확인: `missing`, `not_in_full`.
- `missing` 데이터 행수: 385.
- `not_in_full` 데이터 행수: 0.
- `missing`의 `보유라인목록`에 `WAMAS01` 포함 행: 0.
- `missing`의 `전체데이터등록여부`: 전부 `Y`.

## Claude 자동 회신

- 최초 완료 시 Claude 앱 채팅창 자동 회신 단계가 누락됨.
- 사후 재시도 명령: `auto_reply.py --target claude "[Codex 완료] ..."`
- 결과: FAIL.
- 실패 사유: `Claude window not found`.
- 처리: Claude 창 식별 실패 시 우회 입력하지 않는 규칙에 따라 이 검토기록을 안전망으로 유지.
