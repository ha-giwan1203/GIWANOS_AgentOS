# 2026-06-02 SP3M3 SmartMES rank reorder attempt

## Summary
- Result: FAIL / blocked before jobsetup rerun.
- Target: SmartMES `prod_date=2026-06-02`, `LINE_CD=SP3M3`, 53 rows.
- Desired head: production-plan D+2 day order, rank 1 = `RSP3SC0408`.
- Attempted safest path: ERP D0 `multiListMainSubPrdtPlanRankDecideMng.do` final-save style reorder of existing 53 sGrid rows, no delete and no new rows.

## Read-only evidence
- Source plan: `Z:\15. SP3 메인 CAPA점검\SP3M3\생산지시서\2026년 생산지시\06월\SP3M3_생산지시서_(26.06.02).xlsm`
- Extracted plan rows: 21 rows, 2 Korean rows skipped, cumulative qty 4,025.
- Plan rank 1~5:
  1. `RSP3SC0408` qty 60
  2. `RSP3SC0413` qty 60
  3. `RSP3AC0026` qty 30
  4. `RSP3AC0023` qty 60
  5. `RSP3SC0572` qty 60
- SmartMES before attempt: 53 rows; rank 1 `RSP3SC0644`, rank 2 `RSP3SC0590`, rank 3 `RSP3SC0408`.
- ERP sGrid before attempt: 53 rows; actual D+2 day cluster starts at ERP rank 34 `RSP3SC0408`.

## Proposed reorder
- No missing plan rows from ERP sGrid.
- Proposed first 21 rows:
  `RSP3SC0408`, `RSP3SC0413`, `RSP3AC0026`, `RSP3AC0023`, `RSP3SC0572`, `RSP3AC0024`, `RSP3AC0027`, `RSP3SC0385`, `RSP3SC0383`, `RSP3SC0384`, `RSP3SC0382`, `RSP3PC0054`, `RSP3SE0014`, `RSP3PC0144`, `RSP3PC0143`, `RSP3PC0043`, `RSP3PC0044`, `RSP3SC0396`, `RSP3SC0318`, `RSP3SC0646`, `RSP3PC0130`.
- Duplicate matching rule used: prefer current day cluster rows (`PRDT_RANK >= 34`), then closest qty, then existing rank.

## Irreversible attempt
- One-line irreversible notice was posted, then 30 seconds waited.
- Command: `python .claude/tmp/sp3m3_rank_reorder_20260602.py --apply`
- Preflight save: `sendMesFlag=N`, HTTP 200, `statusCode=200`.
- Final save: `sendMesFlag=Y`, HTTP 200, `statusCode=200`, but `mesMsg={"statusMsg":"추가지시 데이터가 존재하지 않습니다.","statusCode":"350"}`.
- Verification after final save: SmartMES unchanged; rank 1 still `RSP3SC0644`.
- Verification after final save: ERP sGrid unchanged; rank 34 still `RSP3SC0408`.

## Blocker
The D0 final-save endpoint appears to ignore reorder-only payloads when the 53 rows are already `R/P` status and no new `A` additional-instruction row exists. It returns nested MES message `350` and does not update ERP or SmartMES rank.

## Decision
- Did not run jobsetup because rank 1 remained `RSP3SC0644`.
- Did not delete or reinsert rows. That would be a higher-risk C path and could damage already-reflected ERP/MES history.
- Claude needs to decide whether to allow a destructive delete/rebuild path or locate a confirmed SmartMES schedule-rank update API.

## Local files created
- `.claude/tmp/sp3m3_rank_inspect_20260602.py` read-only inspection script.
- `.claude/tmp/sp3m3_rank_reorder_20260602.py` one-off reorder attempt script.
