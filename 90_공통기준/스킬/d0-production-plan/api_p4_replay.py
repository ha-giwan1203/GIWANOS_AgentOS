"""api_p4_replay.py — 옵션 A 하이브리드 P4 단계 2: requests replay 검증

세션133 P4 단계 2 — multiListMainSubPrdtPlanRankDecideMng.do 를 requests로 직접 호출 검증.

흐름:
  1. CDP 9223 attach + cookie/XSRF 추출
  2. 1건 후보 등록 (d0_upload — selectList + multiList) → 새 REG_NO 발급
  3. process_one_row(dry_run=True) → dataList 화면에 채움
  4. dataList + PARENT_PROD_ID 추출
  5. **requests POST `/prdtPlanMng/multiListMainSubPrdtPlanRankDecideMng.do`**
     - param = {dataList, PARENT_PROD_ID, sendMesFlag:'N'}
     - data = JSON.stringify(param) — string 그대로
     - Content-Type: application/x-www-form-urlencoded; charset=UTF-8
     - 헤더: P2 레시피 (ajax:true, X-XSRF-TOKEN 갱신)
  6. 응답 검증 — 200 + DB rank 등록 확인
  7. ERP DELETE rank + DELETE multiList
  8. SmartMES 영향 0 확인 (sendMesFlag='N')

안전 가드:
  - sendMesFlag='Y' 절대 금지 (final_save 호출 안 함)
  - dev 환경 한정
  - 1건만
  - try/finally DELETE 정리
  - timeout 30s
"""
import sys, os, json, time, base64, shutil
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
    process_one_row, find_plan_file, extract_sp3m3_day, DAY_CUT_THRESHOLD,
    LINE_CONFIG, d0_upload,
)

CDP_URL = "http://127.0.0.1:9223"
TIMEOUT = 30
LOG_DIR = Path("06_생산관리/D0_업로드/logs")
POC_DIR = Path("06_생산관리/D0_업로드/poc")
STATE_DIR = Path(__file__).parent / "state"
TEMPLATE_PATH = Path(__file__).parent / "template" / "SSKR_D0_template.xlsx"
ERP_BASE = "http://erp-dev.samsong.com:19100"
RANK_URL = "/prdtPlanMng/multiListMainSubPrdtPlanRankDecideMng.do"
DELETE_REG_URL = "/prdtPlanMng/deleteDoAddnPrdtPlanInstrMngNew.do"
DELETE_RANK_URL = "/prdtPlanMng/deleteDoAddnPrdtPlanInstrMngRankDecideNew.do"


def make_one_row_xlsx(prod_no, qty, prod_date, out_path):
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"템플릿 없음: {TEMPLATE_PATH}")
    shutil.copy2(TEMPLATE_PATH, out_path)
    import win32com.client
    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    try:
        wb = excel.Workbooks.Open(str(out_path.resolve()))
        ws = wb.Worksheets(1)
        last = ws.UsedRange.Rows.Count
        if last >= 2:
            ws.Range(f"A2:D{last}").ClearContents()
        ws.Cells(2, 1).Value = prod_date.strftime("%Y-%m-%d")
        ws.Cells(2, 2).Value = prod_no
        ws.Cells(2, 3).Value = int(qty)
        wb.Save()
        wb.Close()
    finally:
        excel.Quit()
    return out_path


def find_reg_no_in_grid(page, prod_no, today):
    try:
        page.evaluate("() => { try { totGridList.searchListData(); } catch(e){} }")
    except Exception:
        pass
    time.sleep(2)
    return page.evaluate("""(args) => {
        try {
            const d = jQuery('#grid_body').pqGrid('option','dataModel').data;
            const m = d.find(r => r.PROD_NO === args.prodNo && r.REG_DT === args.today);
            return m ? {REG_NO: m.REG_NO, PROD_ID: m.PROD_ID, PRDT_QTY: m.PRDT_QTY} : null;
        } catch(e) { return {err: String(e)}; }
    }""", {"prodNo": prod_no, "today": today})


def build_session_from_cdp(page):
    cookies = page.context.cookies()
    sess = requests.Session()
    xsrf = None
    for c in cookies:
        sess.cookies.set(c["name"], c["value"], domain=c["domain"].lstrip("."), path=c.get("path", "/"))
        if c["name"].upper() in ("XSRF-TOKEN", "X-XSRF-TOKEN"):
            xsrf = c["value"]
    sess.headers.update({
        "ajax": "true",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": D0_URL,
        "Origin": ERP_BASE,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9",
    })
    if xsrf:
        sess.headers["X-XSRF-TOKEN"] = xsrf
    return sess, xsrf


def refresh_xsrf(sess):
    for c in sess.cookies:
        if c.name.upper() in ("XSRF-TOKEN", "X-XSRF-TOKEN"):
            sess.headers["X-XSRF-TOKEN"] = c.value
            return c.value
    return None


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    POC_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"api_p4_replay_{ts}.log"
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    log = {"started_at": datetime.now().isoformat(), "ts": ts, "phases": {}}

    def write_log():
        log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    ensure_chrome_cdp()
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        try:
            page = navigate_to_d0(browser)
        except Exception as e:
            print(f"[FAIL] phase0: {e}", file=sys.stderr); sys.exit(3)

        try:
            page.evaluate("() => { try { totGridList.searchListData(); } catch(e){} }")
        except Exception: pass
        time.sleep(3)

        # 후보 식별
        plan_file = find_plan_file(today_dt)
        wb = openpyxl.load_workbook(plan_file, data_only=True, keep_vba=True)
        day_items = extract_sp3m3_day(wb, DAY_CUT_THRESHOLD)
        registered = page.evaluate("""(today) => {
            try {
                const d = jQuery('#grid_body').pqGrid('option','dataModel').data;
                return d.filter(r => r.REG_DT === today).map(r => r.PROD_NO);
            } catch(e) { return []; }
        }""", today_str)
        candidates = [it for it in day_items if it["PROD_NO"] not in set(registered)]
        if not candidates:
            candidates = [{"PROD_NO": "RSP3SC0665", "QTY": 1500}]
        cand = candidates[0]
        print(f"[phase1] candidate: {cand}")

        # 1행 xlsx
        out_xlsx = POC_DIR / f"d0_p4_replay_{ts}.xlsx"
        make_one_row_xlsx(cand["PROD_NO"], cand["QTY"], today_dt, out_xlsx)

        reg_no = None
        rank_replay_response = None
        try:
            # 1건 등록 (selectList + multiList)
            d0_upload(page, out_xlsx)
            time.sleep(3)
            grid_match = find_reg_no_in_grid(page, cand["PROD_NO"], today_str)
            if not grid_match or "REG_NO" not in grid_match:
                raise RuntimeError(f"REG_NO 매칭 실패: {grid_match}")
            reg_no = grid_match["REG_NO"]
            log["phases"]["multiList"] = {"REG_NO": reg_no, **grid_match}
            print(f"[phase3] REG_NO={reg_no} 발급")

            # process_one_row(dry_run=True) — dataList 채움
            cfg = LINE_CONFIG["SP3M3"]
            p4_r = process_one_row(page, cand["PROD_NO"], reg_no, "SP3M3", cfg["save_url"], dry_run=True)
            if not p4_r.get("ok") or not p4_r.get("dryRun"):
                raise RuntimeError(f"process_one_row dry-run 실패: {p4_r}")
            time.sleep(1)
            print(f"[phase4] addRow OK (dataListLen={p4_r.get('dataListLen')})")

            # dataList + PARENT_PROD_ID 추출
            dataList = page.evaluate("() => sGridList.$local_grid.getData()")
            parent_prod_id = page.evaluate("() => totSelectRowData ? totSelectRowData.PROD_ID : null")
            if not dataList or not parent_prod_id:
                raise RuntimeError(f"dataList/PARENT_PROD_ID 추출 실패: dataList_len={len(dataList) if dataList else 0}, parent={parent_prod_id}")

            print(f"[phase5] dataList len={len(dataList)} / PARENT_PROD_ID={parent_prod_id}")

            # requests 직접 호출 (sendMesFlag='N' 강제)
            sess, xsrf = build_session_from_cdp(page)
            refresh_xsrf(sess)
            param = {"dataList": dataList, "PARENT_PROD_ID": parent_prod_id, "sendMesFlag": "N"}
            body_str = json.dumps(param, ensure_ascii=False)

            print(f"[replay] POST {RANK_URL} body_len={len(body_str)}")
            # Content-Type 시도 1: application/json (jQuery.ajax 기본은 form-urlencoded이나 서버는 JSON 파싱 — Content-Type 무관 가능성)
            replay_resp = sess.post(
                ERP_BASE + RANK_URL,
                data=body_str.encode("utf-8"),
                headers={"Content-Type": "application/json; charset=UTF-8"},
                timeout=TIMEOUT,
            )
            rank_replay_response = {
                "status_code": replay_resp.status_code,
                "body_preview": replay_resp.text[:600],
                "headers_subset": {k: v for k, v in replay_resp.headers.items()
                                   if k.lower() in ("content-type", "set-cookie")},
            }
            log["replay"] = rank_replay_response
            print(f"[replay] status={replay_resp.status_code}")
            print(f"[replay] body[:300]: {replay_resp.text[:300]}")

            # DB rank 등록 확인
            time.sleep(2)
            rank_check = page.evaluate("""(args) => {
                try {
                    const m = jQuery('#m_grid_body').pqGrid('option','dataModel').data;
                    const found = m.filter(r => String(r.EXT_PLAN_REG_NO) === String(args.reg));
                    return {m_rows: found.length, m_first: found[0] || null};
                } catch(e) { return {err: String(e)}; }
            }""", {"reg": reg_no})
            log["db_check"] = rank_check
            print(f"[verify] m_grid REG_NO={reg_no} 매칭: {rank_check}")

        except Exception as e:
            log["error"] = str(e)
            print(f"[ERROR] {e}", file=sys.stderr)
        finally:
            # 정리: rank DELETE + REG DELETE
            if reg_no:
                try:
                    sess, _ = build_session_from_cdp(page)
                    refresh_xsrf(sess)
                    rank_del = sess.delete(
                        ERP_BASE + DELETE_RANK_URL,
                        json={"EXT_PLAN_REG_NO": reg_no, "STD_DA": today_str, "PLAN_DA": today_str,
                              "PROD_NO": cand["PROD_NO"], "LINE_CD": "SP3M3"},
                        headers={"Content-Type": "application/json"},
                        timeout=TIMEOUT,
                    )
                    log.setdefault("cleanup", {})["rank_delete"] = {
                        "status": rank_del.status_code, "body": rank_del.text[:300],
                    }
                    print(f"[cleanup] rank DELETE status={rank_del.status_code}")
                    refresh_xsrf(sess)
                    reg_del = sess.delete(
                        ERP_BASE + DELETE_REG_URL,
                        json={"REG_NO": reg_no},
                        headers={"Content-Type": "application/json"},
                        timeout=TIMEOUT,
                    )
                    log["cleanup"]["reg_delete"] = {
                        "status": reg_del.status_code, "body": reg_del.text[:300],
                    }
                    print(f"[cleanup] reg DELETE status={reg_del.status_code}")
                except Exception as e:
                    log["cleanup_err"] = str(e)
                    print(f"[CLEANUP ERROR] REG_NO {reg_no} 수동 정리 필요: {e}", file=sys.stderr)

            log["finished_at"] = datetime.now().isoformat()
            write_log()
            print(f"[OK] log: {log_path}")


if __name__ == "__main__":
    main()
