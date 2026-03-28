【폴더 목적】
자동차 부품 제조업(삼송 G-ERP) 업무 자동화 폴더.
주요 작업: ERP 라인배치 관리, ZDM 일상점검, 조립비 정산, 생산관리 문서.

【라인배치 자동화 현황】
- 스킬: line-batch-management (현재 v9)
- 작업 대상: 라인구분=OUTER, 제품군=RETRACTOR, 총 674행
- 처리 방식: 검색 없이 상단 그리드 행 순서대로 처리 (runOuterLine)
- ERP URL: http://erp-dev.samsong.com:19100/partLineBatchMng/viewPartLineBatchMng.do
- 탭 ID: 1382924186

【OUTER 라인 입력 규칙 (v9)】
row0 → SD9A01 고정
WEBBING CUTTING → WABAS01
WEBBING ASSY → WAMAS01
D-RING → DRAAS11
ANCHOR ASSY → ANAAS04
SNAP-ON → ANAAS04
LASER MARKING → LTAAS01
INNER BALL GUIDE ASSY → SUB LINE 無
BASE LOCK ASSY → SUB LINE 無
LOCKING ASSY → SUB LINE 無
VEHICLE SENSOR ASSY → SUB LINE 無
INNER SENSOR ASSY → SUB LINE 無

【SELECT 옵션 구조】
LINE_DIV_NM1=OUTER 행: OUTER 라인 코드 목록
LINE_DIV_NM1=SUB 행: SUB LINE 無, BLAAS01 등
LINE_DIV_NM1=MAIN 행: MAIN LINE 無, SD9M1 등
※ 행 타입마다 SELECT 옵션이 완전히 다름

【작업 진행 위치】
- idx119~294 완료 (176건)
- 다음 재개: runOuterLine(295)
- 중지 명령: window._haltAll=true; window._outerInstId=9999;
- 상태 확인: window.outerStatus()

【주의사항】
- 세션 리셋 시 JS 함수(OUTER_RULES, setOuterCell, outerSave, runOuterLine) 반드시 재주입 필요
- 스킬 파일에 최신 코드 포함됨: 업무리스트/line-batch-management.skill
- 작업 시작 전 반드시 현재 done/total 확인 후 재개 위치 확정
- 동기화 금지 구간: 매시 x0:10~13, x0:20~23, x0:30~33, x0:40~43, x0:50~53