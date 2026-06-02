# 2026-06-02 SP3M3 SmartMES rank retry

## 결론
- 결과: FAIL / blocked.
- SmartMES rank update API 후보 `/v2/prdt/schdl/save.api`는 확인했으나 저장 시 `statusCode=823`, `statusMsg=status.823`으로 거절.
- 거절 후 read-only 재조회 결과 SmartMES rank는 변경되지 않음.
- D0 화면/JS에서 별도 `PRDT_RANK` 단일 PATCH endpoint는 발견되지 않음.

## 수행
- 읽은 지시: `.claude/tmp/codex_rank_reorder_retry_20260602.md`
- 보호 대상: `336573~336597`, `337250~337255` 31건.
- 변경 대상: `337270~337286`, `337335~337339` 22건.
- live 조회: 54건.
  - target 22건
  - protected 31건
  - outside 1건: `337343` / `RSP3SC0584` / rank 14

## SmartMES API 탐색
- ClickOnce SmartMES client:
  - `C:\Users\User\AppData\Local\Apps\2.0\CHW58EV7.D3Y\8ZOBDA0X.MLY\mesc..tion_0810baf9b33291d9_07e7.0000_b02e84016d122b59\MESClient.exe`
- ReflectionOnly IL 확인:
  - `ServiceAgent.SaveProductionSchedule(token, List<ScheduleItem>) -> Boolean`
  - endpoint: `v2/prdt/schdl/save.api`
  - body: `JsonConvert.SerializeObject(param)` 후 `RestRequest.AddJsonBody`
  - header: `tid`, `chnl`, `from`, `to`, `lang`, `usrid`, `token`
- UI 저장 로직 확인:
  - `item.oldPrdtRank = item.prdtRank`
  - `item.prdtRank = 1부터 재부여`
  - `changedRank=True`일 때 `SaveProductionSchedule` 호출

## dry-run payload
- 보호 31건과 outside 337343은 rank 변경 0건.
- target 22건만 기존 target slot `[1~13, 46~54]`에 재배치.
- RSP3SC0408은 rank 1로 배치되는 payload.

## apply 결과
```text
[save] http=200 statusCode=823 statusMsg=status.823
RuntimeError: save.api failed: http=200 body={"statusMsg":"status.823","statusCode":823}
```

## 변경 없음 확인
- apply 실패 직후 read-only `/v2/prdt/schdl/list.api` 재조회.
- rank 1~54는 apply 전과 동일.
- RSP3SC0408은 여전히 rank 3.
- 보호 31건도 기존 rank 15~45 그대로.

## D0 endpoint 탐색
- D0 page: `viewListDoAddnPrdtPlanInstrMngNew.do`
- JS: `/js/workspace/pm/prdtPlanMng/listDoAddnPrdtPlanInstrMngNew.js`
- 발견 endpoint:
  - `/prdtPlanMng/deleteDoAddnPrdtPlanInstrMngNew.do`
  - `/prdtPlanMng/deleteDoAddnPrdtPlanInstrMngRankDecideNew.do`
  - `/prdtPlanMng/multiListDoAddnPrdtPlanInstrMngNew.do`
  - `/prdtPlanMng/multiListMainSubPrdtPlanRankDecideMng.do`
  - `/prdtPlanMng/multiListOuterPrdtPlanRankDecideMng.do`
  - `/prdtPlanMng/selectListDoAddnPrdtConctLineDetailNew.do`
  - `/prdtPlanMng/selectListDoAddnPrdtConctLineNew.do`
  - `/prdtPlanMng/selectListDoAddnPrdtPlanInstrMngNew.do`
- 별도 `PRDT_RANK` PATCH/단일 update endpoint 없음.

## 산출 스크립트
- `.claude/tmp/dump_mesclient_il_20260602.ps1`
- `.claude/tmp/scan_mesclient_strings_20260602.py`
- `.claude/tmp/smartmes_schedule_table_20260602.py`
- `.claude/tmp/smartmes_rank_save_20260602.py`
- `.claude/tmp/search_d0_rank_endpoints_20260602.py`
