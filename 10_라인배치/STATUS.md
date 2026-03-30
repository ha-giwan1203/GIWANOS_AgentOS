# 라인배치 진행 현황 (2026-03-31 최신화)

## OUTER 라인 배치
- 스킬: line-batch-management v9
- 작업 대상: OUTER 라인, 674행
- 진행: idx 119~294 완료 (176건)
- 다음 재개: runOuterLine(295)
- ERP URL: http://erp-dev.samsong.com:19100/partLineBatchMng/viewPartLineBatchMng.do
- 탭 ID: 세션별 재확인 필요 (기존 1382924186은 구 세션값, 재접속 시 JS 함수 재주입 필수)

## 동기화 금지 구간
매시 x0:10~13, x0:20~23, x0:30~33, x0:40~43, x0:50~53

## 제어 명령
- 중지: window._haltAll=true; window._outerInstId=9999;
- 상태 확인: window.outerStatus()
- 세션 리셋 시 JS 함수 재주입 필요

## 스킬 패키지 (2026-03-28) — 검증 완료
- v7→v9 기준 전환 완료 (SNAP-ON 추가, LASER MARKING 키워드 단축)
- line-batch-management.skill 생성: 90_공통기준/스킬/ (commit a030ac11)
- v7.md → 98_아카이브/라인배치_스킬문서_v7_archived_20260328.md
- ZIP 구조: line-batch-management/SKILL.md 확인
- OUTER_RULES 6건 / 스모크 테스트 5건 ALL PASS
- **다음 재개: runOuterLine(295)** — ⏸ 잠정 보류 (2026-03-28)
