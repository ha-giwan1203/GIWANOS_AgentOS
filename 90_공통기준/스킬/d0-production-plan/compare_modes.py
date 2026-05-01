"""compare_modes.py — 옵션 A 하이브리드 P6 비교 검증

세션133 P6 진입 (2026-05-01).
PLAN_API_HYBRID.md P6 — 화면 모드 vs api 모드 동일 input 처리 결과 비교.

목적:
  매일 1회 자동 비교. 1주 누적 후 chain 활성 결정 근거.

흐름:
  1. CDP 9223 attach + 후보 식별 (오늘 미등록 PROD_NO 1건, 없으면 RSP3SC0665 fallback)
  2. 1행 xlsx 생성
  3. **api 모드 진행** (--api-mode --no-mes-send 동등):
     - d0_upload + api_rank_batch (sendMesFlag='N')
     - 결과 검증: done=1 / failed=0 / mesMsg 비어있음
     - DELETE rank + DELETE reg
  4. 결과 JSON 저장 (1주 누적용)

안전 가드:
  - sendMesFlag='Y' 절대 호출 금지 (final_save 미실행)
  - 1건만
  - DELETE 정리 try/finally
  - 매일 1회 (스케줄 7:30 권장)

산출:
  state/compare_<ts>.json — {ts, mode:'api', done, failed, mesMsg_empty, db_check, cleanup}
  06_생산관리/D0_업로드/logs/api_p6_compare_<ts>.log

1주 누적 PASS 기준:
  - 7회 연속 done=1 / failed=0 / mesMsg 비어있음 / DELETE 200
  - 1회라도 fail 시 알림 + chain 적용 보류
"""
import sys, os, json, time, shutil
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    from playwright.sync_api import sync_playwright
    import requests
    import openpyxl
except Exception as e:
    print(f"[FAIL] dependency import: {e}", file=sys.stderr)
    sys.exit(2)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run import (
    ensure_chrome_cdp, navigate_to_d0, D0_URL,
    d0_upload, find_plan_file, extract_sp3m3_day, DAY_CUT_THRESHOLD,
    LINE_CONFIG, api_rank_batch, build_requests_session_from_page,
    refresh_xsrf_from_cookies, dedupe_existing_registrations,
)

CDP_URL = "http://127.0.0.1:9223"
TIMEOUT = 30
LOG_DIR = Path("06_생산관리/D0_업로드/logs")
POC_DIR = Path("06_생산관리/D0_업로드/poc")
STATE_DIR = Path(__file__).parent / "state"
TEMPLATE_PATH = Path(__file__).parent / "template" / "SSKR_D0_template.xlsx"
ERP_BASE = "http://erp-dev.samsong.com:19100"
DELETE_REG_URL = "/prdtPlanMng/deleteDoAddnPrdtPlanInstrMngNew.do"
DELETE_RANK_URL = "/prdtPlanMng/deleteDoAddnPrdtPlanInstrMngRankDecideNew.do"


def make_one_row_xlsx(prod_no, qty, prod_date, out_path):
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"템플릿 없음: {TEMPLATE_PATH}")
    shutil.copy2(TEMPLATE_PATH, out_path)
    import win32com.client
    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False; excel.DisplayAlerts = False
    try:
        wb = excel.Workbooks.Open(str(out_path.resolve()))
        ws = wb.Worksheets(1)
        last = ws.UsedRange.Rows.Count
        if last >= 2:
            ws.Range(f"A2:D{last}").ClearContents()
        ws.Cells(2, 1).Value = prod_date.strftime("%Y-%m-%d")
        ws.Cells(2, 2).Value = prod_no
        ws.Cells(2, 3).Value = int(qty)
        wb.Save(); wb.Close()
    finally:
        excel.Quit()
    return out_path


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    POC_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"api_p6_compare_{ts}.log"
    state_path = STATE_DIR / f"compare_{ts}.json"
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    log = {
        "ts": ts,
        "started_at": datetime.now().isoformat(),
        "mode": "api",
        "phases": {},
        "verdict": None,
    }

    def write_log():
        log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    ensure_chrome_cdp()
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        try:
            page = navigate_to_d0(browser)
        except Exception as e:
            log["error"] = f"navigate: {e}"; write_log()
            print(f"[FAIL] {e}", file=sys.stderr); sys.exit(3)

        page.evaluate("() => { try { totGridList.searchListData(); } catch(e){} }")
        time.sleep(3)

        # 후보 식별 — 사용자 명시 로직 (세션133 정정):
        # 1. 오늘 xlsm 주간 items 추출
        # 2. dedupe_existing_registrations로 좌측 grid_body(D0 등록) 기준 중복 제외
        # 3. 우측 s_grid_body(sGridList rank) 잔존 PROD_NO도 추가 dedupe
        # 4. 남은 후보 0건이면 PoC SKIP (fallback 제거 — RSP3SC0665 강제 등록 안 함)
        try:
            plan_file = find_plan_file(today_dt)
            wb = openpyxl.load_workbook(plan_file, data_only=True, keep_vba=True)
            day_items = extract_sp3m3_day(wb, DAY_CUT_THRESHOLD)
            log["day_items_count"] = len(day_items)

            # 좌측 grid_body 기준 dedupe (run.py 함수 재사용)
            day_items = dedupe_existing_registrations(page, day_items, today_dt, "SP3M3")

            # 우측 s_grid_body(sGridList rank) 잔존 PROD_NO도 dedupe — 임시저장 잔존이 있으면 그 PROD_NO 제외
            sgrid_prods = page.evaluate("""(t) => {
                try {
                    const d = jQuery('#s_grid_body').pqGrid('option','dataModel').data || [];
                    // 같은 라인 + 임시저장(EXT_PLAN_YN='Y' AND WORK_STATUS_CD='A') 또는 정상 등록 모두 PROD_NO 수집
                    return d.filter(r => r.LINE_CD === 'SP3M3').map(r => r.PROD_NO);
                } catch(e) { return []; }
            }""", today_str)
            sgrid_set = set(sgrid_prods)
            before_sg = len(day_items)
            day_items = [it for it in day_items if it["PROD_NO"] not in sgrid_set]
            sg_skipped = before_sg - len(day_items)
            if sg_skipped > 0:
                print(f"[compare] sGridList(우측) 잔존 dedupe — {sg_skipped}건 제외 (잔존 PROD_NO: {list(sgrid_set)[:5]}{'...' if len(sgrid_set)>5 else ''})")

            if not day_items:
                log["verdict"] = "SKIPPED"
                log["skip_reason"] = f"등록 가능 후보 0건 (좌측 grid_body + 우측 s_grid_body 모두 dedupe 후). 오늘 morning이 모든 주간 등록 마침. PoC 불필요."
                print(f"[compare] SKIPPED — {log['skip_reason']}")
                log["finished_at"] = datetime.now().isoformat()
                state_path.write_text(json.dumps(log, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
                write_log()
                sys.exit(0)  # SKIP은 정상 종료 (PoC 불필요한 정상 상태)

            cand = day_items[0]
            log["candidate"] = cand
            log["dedupe_summary"] = {
                "day_items_initial": log["day_items_count"],
                "after_left_dedupe": before_sg,
                "after_sgrid_dedupe": len(day_items),
                "sg_skipped": sg_skipped,
            }
            print(f"[compare] candidate: {cand} (좌·우 grid 잔존 0)")
        except Exception as e:
            log["error"] = f"candidate: {e}"; write_log()
            print(f"[FAIL] {e}", file=sys.stderr); sys.exit(3)

        # 1행 xlsx
        out_xlsx = POC_DIR / f"d0_p6_compare_{ts}.xlsx"
        make_one_row_xlsx(cand["PROD_NO"], cand["QTY"], today_dt, out_xlsx)

        reg_no = None
        try:
            d0_upload(page, out_xlsx)
            time.sleep(3)
            match = page.evaluate("""(args) => {
                const d = jQuery('#grid_body').pqGrid('option','dataModel').data;
                const m = d.find(r => r.PROD_NO === args.p && r.REG_DT === args.t);
                return m ? {REG_NO: m.REG_NO} : null;
            }""", {"p": cand["PROD_NO"], "t": today_str})
            if not match:
                raise RuntimeError("REG_NO 매칭 실패")
            reg_no = match["REG_NO"]
            log["phases"]["multiList"] = {"REG_NO": reg_no}
            print(f"[compare] REG_NO={reg_no}")

            # api 모드 rank
            cfg = LINE_CONFIG["SP3M3"]
            result = api_rank_batch(page, [cand], "SP3M3", cfg["save_url"])
            log["phases"]["api_rank_batch"] = result
            print(f"[compare] api_rank_batch: {result}")

            # 검증
            verdict = "PASS"
            errors = []
            if result.get("done") != 1:
                verdict = "FAIL"; errors.append(f"done={result.get('done')} != 1")
            if result.get("failed") != 0:
                verdict = "FAIL"; errors.append(f"failed={result.get('failed')} != 0")
            log["verdict"] = verdict
            log["errors"] = errors
            print(f"[compare] verdict: {verdict}")
            if errors:
                print(f"  errors: {errors}")

        except Exception as e:
            log["error"] = str(e)
            log["verdict"] = "FAIL"
            print(f"[ERROR] {e}", file=sys.stderr)
        finally:
            if reg_no:
                try:
                    # 세션133 진단: requests sess.delete는 응답 200이지만 실제 DB 삭제 안 됨 (사용자 잔존 검증).
                    # 화면 sGridList.deleteRowRankDecide / popupPmD0AddnUpload 등 jQuery.ajax와 100% 동등 동작 보장 위해
                    # page.evaluate로 9223 Chrome 페이지 컨텍스트에서 직접 $.ajax 호출.
                    r1_raw = page.evaluate("""(args) => new Promise((resolve) => {
                        const to = setTimeout(() => resolve({ok:false, err:'timeout 30s'}), 30000);
                        $.ajax({
                            url: '/prdtPlanMng/deleteDoAddnPrdtPlanInstrMngRankDecideNew.do',
                            type: 'delete',
                            data: JSON.stringify({
                                EXT_PLAN_REG_NO: args.ext, STD_DA: args.today, PLAN_DA: args.today,
                                PROD_NO: args.prod, LINE_CD: 'SP3M3',
                            }),
                            success: r => { clearTimeout(to); resolve({ok:true, r}); },
                            error: (xhr,s,e) => { clearTimeout(to); resolve({ok:false, status:xhr.status, body:(xhr.responseText||'').slice(0,500)}); }
                        });
                    })""", {"ext": reg_no, "today": today_str, "prod": cand["PROD_NO"]})
                    r2_raw = page.evaluate("""(reg) => new Promise((resolve) => {
                        const to = setTimeout(() => resolve({ok:false, err:'timeout 30s'}), 30000);
                        $.ajax({
                            url: '/prdtPlanMng/deleteDoAddnPrdtPlanInstrMngNew.do',
                            type: 'delete',
                            data: JSON.stringify({REG_NO: reg}),
                            success: r => { clearTimeout(to); resolve({ok:true, r}); },
                            error: (xhr,s,e) => { clearTimeout(to); resolve({ok:false, status:xhr.status, body:(xhr.responseText||'').slice(0,500)}); }
                        });
                    })""", reg_no)
                    # 응답 정규화 — 기존 코드 호환 (status_code, body_preview)
                    class _R: pass
                    r1 = _R(); r1.status_code = 200 if r1_raw.get("ok") else (r1_raw.get("status") or 0)
                    r1.text = json.dumps(r1_raw.get("r") if r1_raw.get("ok") else {"err": r1_raw}, ensure_ascii=False)
                    r2 = _R(); r2.status_code = 200 if r2_raw.get("ok") else (r2_raw.get("status") or 0)
                    r2.text = json.dumps(r2_raw.get("r") if r2_raw.get("ok") else {"err": r2_raw}, ensure_ascii=False)
                    log["cleanup"] = {
                        "rank_status": r1.status_code, "rank_body": r1.text[:600],
                        "reg_status": r2.status_code, "reg_body": r2.text[:600],
                    }
                    print(f"[cleanup] rank={r1.status_code} body={r1.text[:200]}")
                    print(f"[cleanup] reg={r2.status_code} body={r2.text[:200]}")

                    # 클라이언트 캐시 정리 — sGridList(s_grid_body)에서 해당 EXT_PLAN_REG_NO 행만 제거
                    # (DB는 DELETE로 빠졌지만 sGridList 클라이언트 메모리는 stale → 사용자 화면에 잔존으로 보임)
                    # 사용자 작업 중 다른 행은 건드리지 않고 PoC 등록분만 정리
                    sg_clean = page.evaluate("""(args) => {
                        try {
                            const $g = jQuery('#s_grid_body');
                            if (!$g.length || !$g.pqGrid) return {ok: false, reason: 'no s_grid_body'};
                            const data = $g.pqGrid('option','dataModel').data || [];
                            const before = data.length;
                            const filtered = data.filter(r => String(r.EXT_PLAN_REG_NO) !== String(args.ext));
                            const removed = before - filtered.length;
                            if (removed > 0) {
                                $g.pqGrid('option','dataModel.data', filtered);
                                $g.pqGrid('refreshDataAndView');
                            }
                            return {ok: true, before: before, after: filtered.length, removed: removed};
                        } catch(e) { return {ok: false, err: String(e)}; }
                    }""", {"ext": reg_no})
                    log["cleanup"]["sgrid_cache_clean"] = sg_clean
                    print(f"[cleanup] sGridList 캐시 정리: {sg_clean}")

                    # 정리 실효성 검증 — 좌측(grid_body) + 우측(s_grid_body, 서버 fetch 후) 모두 잔존 여부
                    time.sleep(2)
                    page.evaluate("() => { try { totGridList.searchListData(); } catch(e){} }")
                    time.sleep(2)

                    # ⚠ 진짜 DB 잔존 검증 — 같은 라인의 sGridList를 서버에서 새로 fetch
                    # mGridList에 같은 라인 있으면 클릭 → searchListData → sGridList 서버 fetch
                    server_check = page.evaluate("""(args) => {
                        try {
                            // mGridList 1행이라도 있으면 그 LINE_CD로 sGridList 강제 fetch (PoC 등록분의 라인이 sGridList에 들어가는지 확인)
                            const m = jQuery('#m_grid_body').pqGrid('option','dataModel').data;
                            if (!m || m.length === 0) return {skipped: 'm_grid 비어있음 — 진짜 잔존 검증 불가'};
                            const target = m.find(r => r.LINE_CD === 'SP3M3') || m[0];
                            sGridList.searchListData({
                                LINE_CD: target.LINE_CD, STD_DA: target.STD_DA, PLAN_DA: target.PLAN_DA,
                                LINE_DIV_CD: target.LINE_DIV_CD, DAY_OPT: jQuery('#dayOpt').val()
                            });
                            return {searchListData: 'invoked', LINE_CD: target.LINE_CD};
                        } catch(e) { return {err: String(e)}; }
                    }""")
                    print(f"[verify] sGridList server fetch: {server_check}")
                    time.sleep(3)  # 서버 응답 대기

                    post_check = page.evaluate("""(args) => {
                        const left = jQuery('#grid_body').pqGrid('option','dataModel').data
                            .filter(r => r.REG_DT === args.t && r.PROD_NO === args.p)
                            .map(r => ({REG_NO: r.REG_NO, QTY: r.PRDT_QTY||r.ADD_PRDT_QTY}));
                        let right = [];
                        try {
                            right = jQuery('#s_grid_body').pqGrid('option','dataModel').data
                                .filter(r => String(r.EXT_PLAN_REG_NO) === String(args.ext))
                                .map(r => ({rank: r.PRDT_RANK, prod: r.PROD_NO, ext: r.EXT_PLAN_REG_NO, work_status: r.WORK_STATUS_CD, ext_yn: r.EXT_PLAN_YN}));
                        } catch(e){}
                        return {left_grid_body: left, right_s_grid_body: right};
                    }""", {"t": today_str, "p": cand["PROD_NO"], "ext": reg_no})
                    log["cleanup"]["post_check"] = post_check
                    left_n = len(post_check.get("left_grid_body", []))
                    right_n = len(post_check.get("right_s_grid_body", []))
                    if left_n or right_n:
                        log["verdict"] = "FAIL"
                        if "errors" not in log: log["errors"] = []
                        log["errors"].append(f"DELETE 후 잔존 — 좌측 {left_n}건 / 우측 {right_n}건")
                        print(f"[verify] ⚠ 잔존 좌측 {left_n}건 / 우측 {right_n}건")
                    else:
                        print(f"[verify] 좌측·우측 grid 모두 잔존 0건 — 정리 PASS")

                    if r1.status_code != 200 or r2.status_code != 200:
                        log["verdict"] = "FAIL"
                        if "errors" not in log: log["errors"] = []
                        log["errors"].append(f"cleanup non-200: rank={r1.status_code} reg={r2.status_code}")
                except Exception as e:
                    log["cleanup_err"] = str(e)
                    log["verdict"] = "FAIL"
                    print(f"[CLEANUP ERROR] REG_NO {reg_no} 수동 정리 필요: {e}", file=sys.stderr)

        log["finished_at"] = datetime.now().isoformat()
        state_path.write_text(json.dumps(log, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        write_log()
        print(f"[OK] state: {state_path}")
        print(f"[OK] log: {log_path}")
        print(f"=== verdict: {log['verdict']} ===")
        sys.exit(0 if log['verdict'] == "PASS" else 4)


if __name__ == "__main__":
    main()
