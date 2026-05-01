"""api_p4_capture.py — 옵션 A 하이브리드 P4 단계 1: 페이로드 캡처 PoC

세션133 사용자 명시 P4 진입 (2026-05-01).
PLAN_API_HYBRID.md P4 상세 단계 1 — multiListMainSubPrdtPlanRankDecideMng.do 페이로드 캡처.

목적:
  1) 1건 등록 후 process_one_row(dry_run=True) 호출 → addRow만 수행, jQuery.ajax POST 안 함
  2) sGridList grid 데이터(dataList) + PARENT_PROD_ID 추출
  3) 캡처 결과를 JSON으로 저장 (P4 단계 2 replay용)
  4) ERP DELETE multiList 등록분 정리 (REG_NO 기반) — 자동 정리 try/finally

P4 단계 1 안전 가드:
  - sendMesFlag='Y' 절대 호출 금지 — final_save / multiListMainSubPrdtPlanRankDecideMng POST 모두 안 함
  - dev 환경 한정 (erp-dev.samsong.com)
  - 1건만
  - DELETE 정리 누락 방지 try/finally
  - timeout 30s

산출:
  state/p4_capture_<ts>.json — {dataList, PARENT_PROD_ID, headers, REG_NO}
  06_생산관리/D0_업로드/logs/api_p4_capture_<ts>.log
"""
import sys, os, io, json, time, base64, shutil, subprocess
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
    ensure_chrome_cdp, navigate_to_d0, _safe_goto, D0_URL,
    process_one_row, find_plan_file, extract_sp3m3_day, DAY_CUT_THRESHOLD,
    LINE_CONFIG, d0_upload,
)

CDP_URL = "http://127.0.0.1:9223"
TIMEOUT = 30
LOG_DIR = Path("06_생산관리/D0_업로드/logs")
POC_DIR = Path("06_생산관리/D0_업로드/poc")
STATE_DIR = Path(__file__).parent / "state"
TEMPLATE_PATH = Path(__file__).parent / "template" / "SSKR_D0_template.xlsx"
DELETE_REG_URL = "/prdtPlanMng/deleteDoAddnPrdtPlanInstrMngNew.do"
ERP_BASE = "http://erp-dev.samsong.com:19100"


def make_one_row_xlsx(prod_no: str, qty: int, prod_date: datetime, out_path: Path):
    """1행짜리 ERP D0 템플릿 xlsx — Excel COM 경로 (서버 파서 호환)."""
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


def select_list_upload(page, xlsx_path: Path):
    """selectListPmD0AddnUpload — P3 PoC와 동일 패턴."""
    page.locator("#btnExcelUpload").first.click()
    time.sleep(2)
    ifr = None
    for f in page.frames:
        if "popupPmD0AddnUpload" in (f.url or ""):
            ifr = f
            break
    if ifr is None:
        raise RuntimeError("popup frame 미발견")
    ifr.wait_for_selector("#uploadfrm", timeout=8000)

    with open(xlsx_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    js = """
    async ({b64, filename}) => {
        const bin = atob(b64);
        const bytes = new Uint8Array(bin.length);
        for (let i=0;i<bin.length;i++) bytes[i]=bin.charCodeAt(i);
        const blob = new Blob([bytes], {type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});
        const file = new File([blob], filename, {type: blob.type});
        const form = document.getElementById('uploadfrm');
        const fd = new FormData(form);
        fd.append('files', file);
        const out = await new Promise((resolve) => {
            const to = setTimeout(() => resolve({ok:false, err:'timeout 60s'}), 60000);
            jQuery.ajax({
                type:'POST', url:'/prdtPlanMng/selectListPmD0AddnUpload.do',
                data:fd, processData:false, contentType:false, cache:false,
                success:(res) => { clearTimeout(to); resolve({ok:true, res}); },
                error:(xhr,s,e) => { clearTimeout(to); resolve({ok:false, httpStatus:xhr.status, err:String(e)}); }
            });
        });
        if (!out.ok) return out;
        if (out.res && out.res.data && out.res.data.list && typeof popupPmD0AddnUpload !== 'undefined')
            popupPmD0AddnUpload.excelUploadCallBack(out.res);
        return {ok:true, listLen: out.res?.data?.list?.length, statusCode: out.res.statusCode};
    }
    """
    return ifr, ifr.evaluate(js, {"b64": b64, "filename": xlsx_path.name})


def multi_list_save(ifr):
    js = """
    async () => {
        const dataList = popupPmD0AddnUpload.$local_grid.getData();
        const param = {excelList: dataList, ADDN_PRDT_REASON_CD: document.getElementById('ADDN_PRDT_REASON_CD').value};
        return await new Promise((resolve) => {
            const to = setTimeout(() => resolve({ok:false, err:'timeout 30s'}), 30000);
            jQuery.ajax({
                url: '/prdtPlanMng/multiListPmD0AddnUpload.do', type: 'post',
                data: JSON.stringify(param),
                success: (r) => { clearTimeout(to); resolve({ok:true, r}); },
                error: (xhr,s,e) => { clearTimeout(to); resolve({ok:false, httpStatus:xhr.status, body:(xhr.responseText||'').slice(0,400)}); }
            });
        });
    }
    """
    return ifr.evaluate(js)


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
    log_path = LOG_DIR / f"api_p4_capture_{ts}.log"
    capture_path = STATE_DIR / f"p4_capture_{ts}.json"
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    log = {
        "started_at": datetime.now().isoformat(),
        "ts": ts,
        "phases": {},
    }

    def write_log():
        log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    ensure_chrome_cdp()
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)

        # Phase 0: D0 진입 (run.py navigate_to_d0 활용)
        try:
            page = navigate_to_d0(browser)
            log["phases"]["phase0"] = {"ok": True, "url": page.url}
        except Exception as e:
            log["phases"]["phase0"] = {"ok": False, "err": str(e)}
            write_log()
            print(f"[FAIL] phase0: {e}", file=sys.stderr)
            sys.exit(3)

        # 그리드 강제 로드
        try:
            page.evaluate("() => { try { totGridList.searchListData(); } catch(e){} }")
        except Exception: pass
        time.sleep(3)

        # Phase 1: 후보 식별 — 오늘 미등록 PROD_NO
        try:
            plan_file = find_plan_file(today_dt)
            wb = openpyxl.load_workbook(plan_file, data_only=True, keep_vba=True)
            day_items = extract_sp3m3_day(wb, DAY_CUT_THRESHOLD)
            registered = page.evaluate("""(today) => {
                try {
                    const d = jQuery('#grid_body').pqGrid('option','dataModel').data;
                    return d.filter(r => r.REG_DT === today).map(r => r.PROD_NO);
                } catch(e) { return []; }
            }""", today_str)
            registered_set = set(registered)
            candidates = [it for it in day_items if it["PROD_NO"] not in registered_set]
            if not candidates:
                # 모든 주간 등록됨 → 고정 테스트 후보 (P2 패턴)
                candidates = [{"PROD_NO": "RSP3SC0665", "QTY": 1500}]
            cand = candidates[0]
            log["phases"]["phase1"] = {"ok": True, "candidate": cand, "registered_count": len(registered)}
        except Exception as e:
            log["phases"]["phase1"] = {"ok": False, "err": str(e)}
            write_log()
            print(f"[FAIL] phase1: {e}", file=sys.stderr)
            sys.exit(3)

        # Phase 2: 1행 xlsx 생성
        out_xlsx = POC_DIR / f"d0_p4_oneRow_{ts}.xlsx"
        try:
            make_one_row_xlsx(cand["PROD_NO"], cand["QTY"], today_dt, out_xlsx)
            log["phases"]["phase2"] = {"ok": True, "xlsx": str(out_xlsx)}
        except Exception as e:
            log["phases"]["phase2"] = {"ok": False, "err": str(e)}
            write_log()
            print(f"[FAIL] phase2: {e}", file=sys.stderr)
            sys.exit(3)

        reg_no = None
        captured = None
        try:
            # Phase 3: selectList + multiList (run.py d0_upload 그대로 — popup 확보 robust)
            d0_upload(page, out_xlsx)
            log["phases"]["phase3_d0_upload"] = {"ok": True}
            time.sleep(2)

            grid_match = find_reg_no_in_grid(page, cand["PROD_NO"], today_str)
            log["phases"]["phase3_grid_match"] = grid_match
            if not grid_match or "REG_NO" not in grid_match:
                raise RuntimeError(f"REG_NO grid 매칭 실패: {grid_match}")
            reg_no = grid_match["REG_NO"]

            # Phase 4: process_one_row(dry_run=True) — addRow만, ajax POST 안 함
            #   sGridList에 rowData 채워짐 + jQuery.ajax 호출은 안 됨 (run.py:723 분기)
            cfg = LINE_CONFIG["SP3M3"]
            p4_r = process_one_row(
                page, cand["PROD_NO"], reg_no, "SP3M3",
                cfg["save_url"], dry_run=True,
            )
            log["phases"]["phase4_process_one_row"] = p4_r
            if not p4_r.get("ok") or not p4_r.get("dryRun"):
                raise RuntimeError(f"process_one_row dry-run 실패: {p4_r}")

            # Phase 5: dataList + PARENT_PROD_ID 추출
            time.sleep(1)
            dataList = page.evaluate("() => { try { return sGridList.$local_grid.getData(); } catch(e){return null;} }")
            parent_prod_id = page.evaluate("() => { try { return totSelectRowData ? totSelectRowData.PROD_ID : null; } catch(e){return null;} }")
            day_opt = page.evaluate("() => { try { return jQuery('#dayOpt').val(); } catch(e){return null;} }")

            if not dataList or len(dataList) == 0:
                raise RuntimeError("dataList 추출 실패 (빈 배열)")
            if not parent_prod_id:
                raise RuntimeError("PARENT_PROD_ID 추출 실패")

            captured = {
                "ts": ts,
                "candidate": cand,
                "REG_NO": reg_no,
                "PARENT_PROD_ID": parent_prod_id,
                "dayOpt": day_opt,
                "dataList": dataList,
                "dataList_len": len(dataList),
                "save_url": cfg["save_url"],
                "sendMesFlag": "N",
                "today": today_str,
                "rank_param_template": {
                    "dataList": dataList,
                    "PARENT_PROD_ID": parent_prod_id,
                    "sendMesFlag": "N",
                },
            }

            # 캡처 헤더 정보 (P2 검증된 레시피)
            sess, xsrf = build_session_from_cdp(page)
            captured["session_cookies"] = [c.name for c in sess.cookies]
            captured["xsrf_token_present"] = xsrf is not None
            captured["headers_recipe"] = {k: v for k, v in sess.headers.items()
                                          if k.lower() in ("ajax", "x-xsrf-token", "x-requested-with",
                                                          "referer", "origin", "user-agent", "accept-language")}

            capture_path.write_text(json.dumps(captured, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            log["phases"]["phase5_capture"] = {
                "ok": True,
                "dataList_len": len(dataList),
                "parent_prod_id": parent_prod_id,
                "capture_file": str(capture_path),
            }
            print(f"[OK] capture saved: {capture_path}")
            print(f"  dataList rows: {len(dataList)} / PARENT_PROD_ID={parent_prod_id}")

        except Exception as e:
            log["error"] = str(e)
            print(f"[ERROR] {e}", file=sys.stderr)
        finally:
            # Phase 6: 정리 — multiList 등록분 DELETE (REG_NO 기반)
            # process_one_row dry_run=True 라 rank 행 DB 등록 발생 안 함 → rank DELETE 불필요
            if reg_no:
                try:
                    sess, _ = build_session_from_cdp(page)
                    refresh_xsrf(sess)
                    reg_del = sess.delete(
                        ERP_BASE + DELETE_REG_URL,
                        json={"REG_NO": reg_no},
                        headers={"Content-Type": "application/json"},
                        timeout=TIMEOUT,
                    )
                    log["cleanup"] = {
                        "reg_no": reg_no,
                        "status_code": reg_del.status_code,
                        "body_preview": reg_del.text[:400],
                    }
                    print(f"[cleanup] REG_NO={reg_no} DELETE status={reg_del.status_code}")
                except Exception as e:
                    log["cleanup_err"] = str(e)
                    print(f"[CLEANUP ERROR] REG_NO {reg_no} 수동 정리 필요: {e}", file=sys.stderr)

            log["finished_at"] = datetime.now().isoformat()
            write_log()
            print(f"[OK] log: {log_path}")


if __name__ == "__main__":
    main()
