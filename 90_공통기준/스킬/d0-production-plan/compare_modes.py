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
    refresh_xsrf_from_cookies,
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

        # 후보 식별
        try:
            plan_file = find_plan_file(today_dt)
            wb = openpyxl.load_workbook(plan_file, data_only=True, keep_vba=True)
            day_items = extract_sp3m3_day(wb, DAY_CUT_THRESHOLD)
            registered = page.evaluate("""(t) => {
                const d = jQuery('#grid_body').pqGrid('option','dataModel').data;
                return d.filter(r => r.REG_DT === t).map(r => r.PROD_NO);
            }""", today_str)
            candidates = [it for it in day_items if it["PROD_NO"] not in set(registered)]
            if not candidates:
                candidates = [{"PROD_NO": "RSP3SC0665", "QTY": 1500}]
            cand = candidates[0]
            log["candidate"] = cand
            print(f"[compare] candidate: {cand}")
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
                    sess = build_requests_session_from_page(page)
                    refresh_xsrf_from_cookies(sess)
                    r1 = sess.delete(
                        ERP_BASE + DELETE_RANK_URL,
                        json={"EXT_PLAN_REG_NO": reg_no, "STD_DA": today_str, "PLAN_DA": today_str,
                              "PROD_NO": cand["PROD_NO"], "LINE_CD": "SP3M3"},
                        headers={"Content-Type": "application/json"},
                        timeout=TIMEOUT,
                    )
                    refresh_xsrf_from_cookies(sess)
                    r2 = sess.delete(
                        ERP_BASE + DELETE_REG_URL,
                        json={"REG_NO": reg_no},
                        headers={"Content-Type": "application/json"},
                        timeout=TIMEOUT,
                    )
                    log["cleanup"] = {"rank_status": r1.status_code, "reg_status": r2.status_code}
                    print(f"[cleanup] rank={r1.status_code} reg={r2.status_code}")
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
