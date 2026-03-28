# 라인배치 진행 현황 (2026-03-22)

## OUTER 라인 배치
- 스킬: line-batch-management v9
- 작업 대상: OUTER 라인, 674행
- 진행: idx 119~294 완료 (176건)
- 다음 재개: runOuterLine(295)
- ERP URL: http://erp-dev.samsong.com:19100/partLineBatchMng/viewPartLineBatchMng.do
- 탭 ID: 1382924186

## 동기화 금지 구간
매시 x0:10~13, x0:20~23, x0:30~33, x0:40~43, x0:50~53

## 제어 명령
- 중지: window._haltAll=true; window._outerInstId=9999;
- 상태 확인: window.outerStatus()
- 세션 리셋 시 JS 함수 재주입 필요
