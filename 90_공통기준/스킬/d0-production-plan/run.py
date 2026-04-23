"""/d0-plan — ERP D0추가생산지시 자동화 (SP3M3 MAIN + SD9A01 OUTER).

세션별 업로드:
  저녁 (evening): SP3M3 야간 + SD9A01 OUTER D+1 (생산일 = 내일)
  아침 (morning): SP3M3 주간 (생산일 = 내일, 누적 ≥ 3600 컷)

실행:
  python run.py --session evening
  python run.py --session morning
  python run.py --session auto --dry-run
  python run.py --session evening --line SP3M3
"""
import sys, io, os, re, json, time, base64, argparse, subprocess
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import openpyxl
from playwright.sync_api import sync_playwright
import pyautogui

# ============================================================
# 설정
# ============================================================
CDP_URL = "http://localhost:9222"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CHROME_PROFILE = r"C:\Users\User\.flow-chrome-debug"
ERP_LAYOUT = "http://erp-dev.samsong.com:19100/layout/layout.do"
D0_URL = "http://erp-dev.samsong.com:19100/prdtPlanMng/viewListDoAddnPrdtPlanInstrMngNew.do"
OAUTH_LOGIN = "http://auth-dev.samsong.com:18100/login"
PLAN_ROOT = r"Z:\15. SP3 메인 CAPA점검\SP3M3\생산지시서"
REPO_ROOT = Path(__file__).parent.parent.parent.parent
UPLOAD_DIR = REPO_ROOT / "06_생산관리" / "D0_업로드"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SMARTMES_TOKEN = "bfee3f3d-caf9-434d-abbb-2cb015ec2469"
SMARTMES_BASE = "http://lmes-dev.samsong.com:19220"
DAY_CUT_THRESHOLD = 3600

LINE_CONFIG = {
    "SP3M3": {
        "line_div_cd": "02",
        "save_url": "/prdtPlanMng/multiListMainSubPrdtPlanRankDecideMng.do",
    },
    "SD9A01": {
        "line_div_cd": "01",
        "save_url": "/prdtPlanMng/multiListOuterPrdtPlanRankDecideMng.do",
    },
}


# ============================================================
# Phase 0: 환경 준비
# ============================================================
def ensure_chrome_cdp():
    """CDP 9222 기동 확인."""
    import urllib.request
    try:
        urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=3)
        print("[phase0] CDP 9222 alive")
        return True
    except Exception:
        print("[phase0] CDP dead — launching Chrome")

    subprocess.Popen([
        CHROME_PATH,
        f"--remote-debugging-port=9222",
        f"--user-data-dir={CHROME_PROFILE}",
        "--no-first-run", "--no-default-browser-check",
        ERP_LAYOUT,
    ])
    for i in range(10):
        time.sleep(1.5)
        try:
            urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=2)
            print(f"[phase0] CDP up (try={i+1})")
            return True
        except Exception:
            continue
    raise RuntimeError("CDP 9222 기동 실패")


def ensure_erp_login(page):
    """auth-dev 로그인 페이지면 자동 로그인."""
    if "auth-dev.samsong.com" in page.url and "/login" in page.url:
        print("[phase0] OAuth 로그인 수행")
        page.bring_to_front()
        time.sleep(1.0)
        page.wait_for_selector('input[name="userId"]', timeout=10000)
        info = page.evaluate("() => ({screenX: window.screenX, screenY: window.screenY, chromeH: window.outerHeight - window.innerHeight})")
        box = page.locator('input[name="userId"]').bounding_box()
        sx = int(info["screenX"] + box["x"] + box["width"] / 2)
        sy = int(info["screenY"] + info["chromeH"] + box["y"] + box["height"] / 2)
        pyautogui.click(sx, sy); time.sleep(1.5)
        pyautogui.press("down"); time.sleep(0.5)
        pyautogui.press("return"); time.sleep(1.5)
        page.locator("button[type=submit]").first.click()
        time.sleep(5)


def navigate_to_d0(browser):
    """D0추가생산지시 화면 탭 확보."""
    ctx = browser.contexts[0]
    page = None
    for pg in ctx.pages:
        if "viewListDoAddnPrdtPlanInstrMngNew" in pg.url:
            page = pg; break
    if page is None:
        for pg in ctx.pages:
            if pg.url.startswith("http"):
                page = pg; break
    if page is None:
        raise RuntimeError("사용 가능한 탭 없음")

    page.bring_to_front()
    ensure_erp_login(page)

    # OAuth 로그인 후 리다이렉트 완료 대기 (erp-dev.samsong.com 도착까지)
    for _ in range(20):
        if "erp-dev.samsong.com" in page.url:
            break
        time.sleep(0.5)
    try: page.wait_for_load_state("domcontentloaded", timeout=15000)
    except Exception: pass
    time.sleep(2)

    if "viewListDoAddnPrdtPlanInstrMngNew" not in page.url:
        try:
            page.goto(D0_URL, timeout=30000)
        except Exception as e:
            # 네비게이션 충돌 시 재시도
            print(f"[phase0] goto 재시도 사유: {e}")
            time.sleep(3)
            page.goto(D0_URL, timeout=30000)
        try: page.wait_for_load_state("domcontentloaded", timeout=20000)
        except Exception: pass
        time.sleep(3)
    print(f"[phase0] D0 화면 진입: {page.url}")
    return page


# ============================================================
# Phase 1: 파일 해석
# ============================================================
def find_plan_file(target_date: datetime) -> Path:
    folder = Path(PLAN_ROOT) / f"{target_date.year}년 생산지시" / f"{target_date.month:02d}월"
    if not folder.exists():
        raise FileNotFoundError(f"폴더 없음: {folder}")
    date_tag = f"{target_date.year%100:02d}.{target_date.month:02d}.{target_date.day:02d}"
    candidates = list(folder.glob(f"SP3M3_생산지시서_({date_tag})*.xlsm"))
    if not candidates:
        raise FileNotFoundError(f"파일 없음: {folder}/SP3M3_생산지시서_({date_tag})*.xlsm")
    # 수정본 우선 (mtime 최신)
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    chosen = candidates[0]
    print(f"[phase1] 파일 선택: {chosen.name}")
    return chosen


def _find_section_end(ws, start_row, next_header_keyword=None):
    """start_row부터 시작해서 다음 헤더 또는 빈 행 만날 때까지의 끝 행."""
    r = start_row
    last = start_row
    while r <= ws.max_row:
        b = ws.cell(row=r, column=2).value
        i = ws.cell(row=r, column=9).value
        k = ws.cell(row=r, column=11).value
        # 다음 섹션 헤더 만나면 중단
        if b and next_header_keyword and next_header_keyword in str(b):
            break
        if i and k:
            last = r
        r += 1
    return last


def extract_sp3m3_night(wb):
    """출력용 시트 야간 섹션."""
    ws = wb["출력용"]
    # R1 헤더 '◀ D+1 야간계획', R35 근처 주간 헤더
    start = 3  # R3부터 데이터
    night_end = 34  # 보수적 (헤더 R35 전)
    # 동적 탐지
    for r in range(2, ws.max_row+1):
        v = ws.cell(row=r, column=2).value
        if v and "주간계획" in str(v):
            night_end = r - 1
            break
    items = []
    for r in range(start, night_end+1):
        part = ws.cell(row=r, column=9).value  # I
        qty = ws.cell(row=r, column=11).value  # K
        if part and qty:
            items.append({"PROD_NO": str(part).strip(), "QTY": int(qty)})
    print(f"[phase1] SP3M3 야간: {len(items)}건")
    return items


def extract_sp3m3_day(wb, cut_threshold=DAY_CUT_THRESHOLD):
    """출력용 시트 주간 섹션 — 누적 ≥ cut_threshold 첫 행까지 포함."""
    ws = wb["출력용"]
    day_start = None
    for r in range(2, ws.max_row+1):
        v = ws.cell(row=r, column=2).value
        if v and "주간계획" in str(v):
            day_start = r + 1
            break
    if day_start is None:
        raise ValueError("출력용 시트 주간 헤더 미발견")
    items = []
    cumsum = 0
    for r in range(day_start, ws.max_row+1):
        part = ws.cell(row=r, column=9).value
        qty = ws.cell(row=r, column=11).value
        if not (part and qty):
            continue
        items.append({"PROD_NO": str(part).strip(), "QTY": int(qty)})
        cumsum += int(qty)
        if cumsum >= cut_threshold:
            print(f"[phase1] SP3M3 주간 컷: 누적 {cumsum} ({len(items)}건)")
            break
    else:
        print(f"[phase1] SP3M3 주간: 누적 {cumsum} (컷 미도달, 전량 {len(items)}건)")
    return items


def extract_outer_d1(wb, target_line="SD9M01"):
    """OUTER 생산계획 시트 D+1 블록에서 B열 == target_line 필터."""
    ws = wb["OUTER 생산계획"]
    items = []
    for r in range(2, ws.max_row+1):
        b = ws.cell(row=r, column=2).value  # D+1 라인
        d = ws.cell(row=r, column=4).value  # 품번 (접미사 포함)
        e = ws.cell(row=r, column=5).value  # 수량
        if b and str(b).strip() == target_line and d and e:
            items.append({"PROD_NO": str(d).strip(), "QTY": int(e)})
    print(f"[phase1] SD9A01 OUTER D+1: {len(items)}건")
    return items


# ============================================================
# Phase 2: 업로드 엑셀 생성
# ============================================================
def _load_items_from_xlsx(xlsx_path: Path):
    """외부 엑셀 파일에서 (생산일/제품번호/생산량) 추출."""
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb.active
    items = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row and row[1] and row[2]:
            items.append({"PROD_NO": str(row[1]).strip(), "QTY": int(row[2])})
    return items


def _extract_prod_date(items):
    """items는 PROD_NO/QTY만 — 외부 엑셀 원본에서 생산일 재추출."""
    return None  # caller에서 fallback


def make_upload_xlsx(items, prod_date: datetime, out_path: Path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["생산일", "제품번호", "생산량"])
    for it in items:
        ws.append([prod_date.strftime("%Y-%m-%d"), it["PROD_NO"], it["QTY"]])
    wb.save(out_path)
    print(f"[phase2] 업로드 엑셀 생성: {out_path.name} ({len(items)}건)")


# ============================================================
# Phase 3: D0 업로드 (selectList + multiList)
# ============================================================
def d0_upload(page, xlsx_path: Path):
    """팝업 오픈 → selectList → multiList."""
    # 페이지 로드 확인 + 버튼 대기
    try:
        page.wait_for_selector("#btnExcelUpload", timeout=15000)
    except Exception:
        print(f"[phase3] #btnExcelUpload 대기 실패 — 현재 URL: {page.url}")
        raise

    # 팝업 오픈
    ifr = None
    for fr in page.frames:
        if "popupPmD0AddnUpload" in fr.url:
            ifr = fr; break
    if ifr is None:
        # 클릭 재시도 (최대 3번)
        for attempt in range(3):
            try:
                page.locator("#btnExcelUpload").first.click()
            except Exception as e:
                print(f"[phase3] 클릭 실패 try={attempt+1}: {e}")
                time.sleep(2)
                continue
            # popup 로드 대기 (최대 12초)
            for _ in range(24):
                time.sleep(0.5)
                for fr in page.frames:
                    if "popupPmD0AddnUpload" in fr.url:
                        ifr = fr; break
                if ifr: break
            if ifr: break
            print(f"[phase3] popup 미등장 try={attempt+1} — 재시도")
            time.sleep(2)
    if ifr is None:
        raise RuntimeError("Excel Upload 팝업 확보 실패 (3회 재시도 실패)")
    try:
        ifr.wait_for_load_state("domcontentloaded", timeout=8000)
        ifr.wait_for_selector("#uploadfrm", timeout=8000)
    except Exception: pass
    print(f"[phase3] popup open: {ifr.url}")

    with open(xlsx_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    # selectList
    parse_js = """
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
            const to = setTimeout(() => resolve({ok:false, err:'timeout 20s'}), 20000);
            jQuery.ajax({
                type:'POST', url:'/prdtPlanMng/selectListPmD0AddnUpload.do',
                data:fd, processData:false, contentType:false, cache:false,
                success:(res) => { clearTimeout(to); resolve({ok:true, res}); },
                error:(xhr,s,e) => { clearTimeout(to); resolve({ok:false, httpStatus:xhr.status, err:String(e), body:(xhr.responseText||'').slice(0,400)}); }
            });
        });
        if (!out.ok) return out;
        const res = out.res;
        if (res && res.data && res.data.list && typeof popupPmD0AddnUpload !== 'undefined') {
            popupPmD0AddnUpload.excelUploadCallBack(res);
        }
        return {ok:true, listLen: res && res.data && res.data.list ? res.data.list.length : null, statusCode: res.statusCode, statusTxt: res.statusTxt};
    }
    """
    r = ifr.evaluate(parse_js, {"b64": b64, "filename": xlsx_path.name})
    print(f"[phase3 parse] {r}")
    if not r.get("ok") or not r.get("listLen"):
        raise RuntimeError(f"selectList 실패: {r}")

    # 오류 행 검증
    err_check = ifr.evaluate("() => { try { return popupPmD0AddnUpload.$local_grid.getData().filter(r => r.ERROR_FLAG).length; } catch(e){ return -1; } }")
    if err_check > 0:
        raise RuntimeError(f"오류 행 {err_check}건 존재")

    # multiList (DB 저장)
    save_js = """
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
    r2 = ifr.evaluate(save_js)
    print(f"[phase3 save] {r2}")
    if not r2.get("ok") or str((r2.get("r") or {}).get("statusCode")) != "200":
        raise RuntimeError(f"multiListPmD0AddnUpload 실패: {r2}")

    # 본 그리드 갱신 + 팝업 닫기
    try:
        ifr.evaluate("""() => {
            try {
                if (parent.totGridList && parent.totGridList.searchListData) parent.totGridList.searchListData();
                if (parent.$ && parent.$('#popupPmD0AddnUpload').dialog) parent.$('#popupPmD0AddnUpload').dialog('close');
            } catch(e){}
        }""")
    except Exception: pass
    time.sleep(3)
    print("[phase3] D0 업로드 완료")


# ============================================================
# Phase 4: 야간 서열 배치
# ============================================================
def process_one_row(page, prod_no, target_ext_reg, target_line, save_url, dry_run=False):
    """한 품번 처리: 상단 클릭 → m 선택 → s 로드 → addRow → multiList 임시저장."""
    # 1. rowClick 로직 재현
    click_r = page.evaluate("""(args) => {
        const d = jQuery('#grid_body').pqGrid('option','dataModel').data;
        const idx = d.findIndex(r => r.PROD_NO === args.prodNo && String(r.REG_NO) === String(args.extReg));
        if (idx < 0) return {ok:false, reason:'상단 매칭 실패'};
        const rowData = d[idx];
        if (!rowData.REG_NO) return {ok:false, reason:'REG_NO 없음'};

        window.mSelectRowData = null;
        try { sGridList.$local_grid.options.dataModel.data = []; sGridList.$local_grid.refreshView(); } catch(e){}
        jQuery('#sendMesFlag').val('N');
        window.totSelectRowData = rowData;
        const param = {
            PROD_ID: rowData.PROD_ID, PLAN_DA: rowData.REG_DT, PRDT_QTY: rowData.PRDT_QTY,
            SHIPTDA: rowData.SHIPTDA, EXT_PLAN_REG_NO: rowData.REG_NO, DAY_OPT: jQuery('#dayOpt').val()
        };
        try { mGridList.$local_grid.options.dataModel.data = []; mGridList.$local_grid.refreshView(); } catch(e){}
        mGridList.searchListData(param);
        return {ok:true, idx, prodId: rowData.PROD_ID};
    }""", {"prodNo": prod_no, "extReg": str(target_ext_reg)})
    if not click_r.get("ok"):
        return {"ok":False, "stage":"top_click", "err":click_r.get("reason")}

    # m_grid 로드 대기
    for _ in range(16):
        time.sleep(0.5)
        if page.evaluate("""(e) => { try { return jQuery('#m_grid_body').pqGrid('option','dataModel').data.some(r => String(r.EXT_PLAN_REG_NO) === String(e)); } catch(err){return false;} }""", str(target_ext_reg)):
            break
    else:
        return {"ok":False, "stage":"m_wait"}

    # 2. 라인 선택
    m_r = page.evaluate("""(targetLine) => {
        const m = jQuery('#m_grid_body').pqGrid('option','dataModel').data;
        const idx = m.findIndex(r => r.LINE_CD === targetLine);
        if (idx < 0) return {ok:false, reason:'line 없음', avail:m.map(r=>r.LINE_CD)};
        const rowData = m[idx];
        window.mSelectRowData = rowData;
        try {
            sGridList.searchListData({
                LINE_CD:rowData.LINE_CD, STD_DA:rowData.STD_DA, PLAN_DA:rowData.PLAN_DA,
                LINE_DIV_CD:rowData.LINE_DIV_CD, DAY_OPT:jQuery('#dayOpt').val()
            });
        } catch(e) { return {ok:false, reason:'sGridList err: '+e.message}; }
        return {ok:true, lineDivCd: rowData.LINE_DIV_CD};
    }""", target_line)
    if not m_r.get("ok"):
        return {"ok":False, "stage":"m_select", "err":m_r.get("reason"), "avail":m_r.get("avail")}

    # s_grid 로드 대기 — 고정 3초 (0건이어도 OK, 주간 초기 상황 대응)
    time.sleep(3)
    s_rows = page.evaluate("() => { try { return sGridList.$local_grid.pdata.length; } catch(e){return -1;} }")
    if s_rows < 0:
        return {"ok":False, "stage":"s_wait", "rows":s_rows, "err":"s_grid 미초기화"}

    # 3. addRow 인라인 + 임시저장
    save_js = """
    async (args) => {
        if (!mSelectRowData || mSelectRowData.LINE_CD !== args.targetLine) return {ok:false, reason:'mSelect err'};
        const m = mSelectRowData;
        if (!m.MPRDTN_DIV_CD) return {ok:false, reason:'MPRDTN_DIV_CD 공란'};
        if (!m.PRDT_CATE_CD) return {ok:false, reason:'PRDT_CATE_CD 공란'};

        const rowData = Object.assign({}, m);
        rowData.DAY_OPT          = jQuery('#dayOpt').val();
        rowData.WORK_STATUS_CD   = 'A';
        rowData.WORK_STATUS_NM   = '추가';
        rowData.EXT_PLAN_YN      = 'Y';
        rowData.EXT_PLAN_REG_NO  = m.EXT_PLAN_REG_NO;
        rowData.LINE_NM          = m.LINE_NM; rowData.LINE_CD = m.LINE_CD;
        rowData.PROD_NO          = m.PROD_NO; rowData.PROD_NM = m.PROD_NM; rowData.PROD_REV = m.PROD_REV;
        rowData.PRDT_PLAN_QTY    = m.ADD_PRDT_QTY; rowData.OLD_PRDT_PLAN_QTY = m.ADD_PRDT_QTY;
        rowData.NEXT_PLAN_DA     = m.NEXT_PLAN_DA;

        const addRowIndx = sGridList.$local_grid.pdata.length;
        sGridList.$local_grid.addRow({rowData: rowData, checkEditable:false, rowIndx: addRowIndx});
        sGridList.setBeginTime();

        if (args.dryRun) return {ok:true, dryRun:true, addedRank: rowData.PRDT_RANK, dataListLen: sGridList.$local_grid.getData().length};

        const dataList = sGridList.$local_grid.getData();
        jQuery('#sendMesFlag').val('N');
        const param = JSON.stringify({dataList, PARENT_PROD_ID: totSelectRowData.PROD_ID, sendMesFlag:'N'});
        const out = await new Promise((resolve) => {
            const to = setTimeout(() => resolve({ok:false, err:'timeout 30s'}), 30000);
            jQuery.ajax({
                url: args.saveUrl, type:'post', data: param,
                success: r => { clearTimeout(to); resolve({ok:true, r}); },
                error: (xhr,s,e) => { clearTimeout(to); resolve({ok:false, httpStatus:xhr.status, body:(xhr.responseText||'').slice(0,400)}); }
            });
        });
        return Object.assign({addedRank: rowData.PRDT_RANK, dataListLen: dataList.length}, out);
    }
    """
    r = page.evaluate(save_js, {"targetLine": target_line, "saveUrl": save_url, "dryRun": dry_run})
    return r


def rank_batch(page, items, target_line, save_url, dry_run=False):
    """엑셀 순서대로 상단 idx 매핑 → process_one_row 반복."""
    # 상단 grid REG_NO 최대 매핑
    idx_map = page.evaluate("""(today) => {
        const d = jQuery('#grid_body').pqGrid('option','dataModel').data;
        const map = {};
        for (let i=0;i<d.length;i++) {
            if (d[i].REG_DT !== today) continue;
            const pno = d[i].PROD_NO;
            if (!map[pno] || Number(d[i].REG_NO) > Number(map[pno].extReg)) {
                map[pno] = {idx:i, extReg:d[i].REG_NO};
            }
        }
        return map;
    }""", datetime.today().strftime("%Y-%m-%d"))

    done, failed, missing = 0, 0, 0
    fails = []
    for it in items:
        pno = it["PROD_NO"]
        if pno not in idx_map:
            print(f"[phase4] SKIP missing in grid: {pno}")
            missing += 1; continue
        ext = idx_map[pno]["extReg"]
        r = process_one_row(page, pno, ext, target_line, save_url, dry_run=dry_run)
        ok = r.get("ok") and (r.get("dryRun") or (r.get("r") and str(r["r"].get("statusCode"))=="200"))
        print(f"[phase4] {pno} ext={ext} -> {'OK' if ok else 'FAIL'}")
        if ok: done += 1
        else:
            failed += 1
            fails.append({"pno":pno, "ext":ext, "result":r})
            if failed >= 3: print("[phase4] 3회 연속 실패 — 중단"); break
        time.sleep(1.2)
    return {"done":done, "failed":failed, "missing":missing, "fails":fails}


# ============================================================
# Phase 5: 최종 저장 (MES 전송)
# ============================================================
def final_save(page, save_url):
    js = """
    async (args) => {
        jQuery('#sendMesFlag').val('Y');
        sGridList.setBeginTime();
        const dataList = sGridList.$local_grid.getData();
        const param = JSON.stringify({dataList, PARENT_PROD_ID: totSelectRowData.PROD_ID, sendMesFlag:'Y'});
        return await new Promise((resolve) => {
            const to = setTimeout(() => resolve({ok:false, err:'timeout 60s'}), 60000);
            jQuery.ajax({
                url: args.saveUrl, type:'post', data: param,
                success: r => { clearTimeout(to); resolve({ok:true, r}); },
                error: (xhr,s,e) => { clearTimeout(to); resolve({ok:false, httpStatus:xhr.status, body:(xhr.responseText||'').slice(0,400)}); }
            });
        });
    }
    """
    r = page.evaluate(js, {"saveUrl": save_url})
    print(f"[phase5 final_save] {r}")
    if not r.get("ok") or str((r.get("r") or {}).get("statusCode")) != "200":
        raise RuntimeError(f"최종 저장 실패: {r}")
    return r["r"]


# ============================================================
# Phase 6: SmartMES 검증
# ============================================================
def verify_smartmes(line_cd: str, prdt_da: datetime, excel_order: list):
    import urllib.request
    headers = {
        "Authorization": f"Bearer {SMARTMES_TOKEN}",
        "tid": SMARTMES_TOKEN, "token": SMARTMES_TOKEN,
        "chnl": "MES", "from": "MESClient", "to": "MES",
        "usrid": "lmes", "Content-Type": "application/json",
    }
    body = json.dumps({"lineCd": line_cd, "prdtDa": prdt_da.strftime("%Y%m%d")}).encode()
    req = urllib.request.Request(f"{SMARTMES_BASE}/v2/prdt/schdl/list.api", data=body, headers=headers)
    try:
        items = json.loads(urllib.request.urlopen(req, timeout=5).read())["rslt"]["items"]
    except Exception as e:
        print(f"[phase6] SmartMES 조회 실패: {e}")
        return
    r_items = sorted([x for x in items if x["workStatusCd"] == "R"], key=lambda i: i["prdtRank"])
    pnos_server = [x["pno"] for x in r_items]
    pnos_excel = [it["PROD_NO"] for it in excel_order]
    # 엑셀 순서 기준으로 서버의 R 리스트 일치 여부
    filtered_server = [p for p in pnos_server if p in set(pnos_excel)]
    filtered_excel = [p for p in pnos_excel if p in set(pnos_server)]
    if filtered_server == filtered_excel:
        print(f"[phase6] {line_cd} 서열 순서 엑셀 일치 ✅ ({len(filtered_server)}건)")
    else:
        print(f"[phase6] {line_cd} 서열 불일치")
        print(f"  server: {filtered_server[:10]}...")
        print(f"  excel : {filtered_excel[:10]}...")


# ============================================================
# 세션 실행
# ============================================================
def run_session_line(page, wb, line, items, prod_date, dry_run):
    if not items:
        print(f"[{line}] 추출 0건 — 스킵")
        return
    cfg = LINE_CONFIG[line]
    xlsx = UPLOAD_DIR / f"d0_{line}_{prod_date.strftime('%Y%m%d')}.xlsx"
    make_upload_xlsx(items, prod_date, xlsx)

    if dry_run:
        print(f"[{line}] dry-run: 엑셀 생성까지만 (추출 {len(items)}건)")
        return

    d0_upload(page, xlsx)
    target_line = "SP3M3" if line == "SP3M3" else "SD9A01"
    batch = rank_batch(page, items, target_line, cfg["save_url"], dry_run=False)
    print(f"[{line}] rank_batch: {batch}")
    if batch["failed"] > 0:
        print(f"[{line}] 실패 존재 — 최종 저장 보류")
        return
    final_save(page, cfg["save_url"])
    verify_smartmes(target_line, prod_date, items)


def determine_session(arg):
    if arg != "auto":
        return arg
    h = datetime.now().hour
    if 6 <= h <= 10: return "morning"
    if 15 <= h <= 22: return "evening"
    raise ValueError(f"시간대({h}시)로 세션 자동 판정 불가 — 명시 지정 필요")


# ============================================================
# 메인
# ============================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", choices=["evening","morning","auto"], required=True)
    ap.add_argument("--line", choices=["SP3M3","SD9A01","ALL"], default="ALL")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--target-date", help="YYYY-MM-DD 파일명 날짜 (기본 자동)")
    ap.add_argument("--xlsx", help="업로드용 엑셀 파일 경로 직접 지정 (Phase 1 추출 건너뛰기)")
    ap.add_argument("--skip-upload", action="store_true", help="Phase 3 D0 업로드 건너뛰기 (이미 상단에 등록된 경우 Phase 4부터)")
    args = ap.parse_args()

    session = determine_session(args.session)
    print(f"=== /d0-plan session={session} line={args.line} dry_run={args.dry_run} ===")

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if args.target_date:
        target_file_date = datetime.strptime(args.target_date, "%Y-%m-%d")
    else:
        target_file_date = today + timedelta(days=1) if session == "evening" else today
    print(f"파일명 날짜(target_file_date) = {target_file_date.strftime('%Y-%m-%d')}")

    # Phase 0
    ensure_chrome_cdp()
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        page = navigate_to_d0(browser)

        # --xlsx 직접 사용 모드: Phase 1 추출 건너뛰고 그대로 업로드
        if args.xlsx:
            xlsx_path = Path(args.xlsx)
            if not xlsx_path.exists():
                raise FileNotFoundError(f"--xlsx 파일 없음: {xlsx_path}")
            items = _load_items_from_xlsx(xlsx_path)
            prod_date = _extract_prod_date(items) or target_file_date
            line_override = args.line if args.line != "ALL" else "SP3M3"
            print(f"[direct] xlsx={xlsx_path.name} items={len(items)} line={line_override} prod_date={prod_date.strftime('%Y-%m-%d')}")
            if args.dry_run:
                print("[direct] dry-run: 엑셀 확인까지만")
                return
            # xlsx 그대로 업로드 (Phase 3) + 서열 배치 (Phase 4) + 최종 저장 (Phase 5)
            if args.skip_upload:
                print("[direct] --skip-upload: Phase 3 건너뜀")
            else:
                d0_upload(page, xlsx_path)
            cfg = LINE_CONFIG[line_override]
            batch = rank_batch(page, items, line_override, cfg["save_url"], dry_run=False)
            print(f"[direct] rank_batch: {batch}")
            if batch["failed"] > 0:
                print("[direct] 실패 존재 — 최종 저장 보류"); return
            final_save(page, cfg["save_url"])
            verify_smartmes(line_override, prod_date, items)
            print("=== /d0-plan --xlsx 완료 ===")
            return

        # Phase 1: 파일
        plan_path = find_plan_file(target_file_date)
        wb = openpyxl.load_workbook(plan_path, data_only=True, keep_vba=True)

        if session == "evening":
            # SP3M3 야간: ERP 생산일 = 파일명 날짜 - 1 (야간 시작일 = 오늘)
            # SD9A01 OUTER: ERP 생산일 = 파일명 날짜 (내일)
            if args.line in ("SP3M3","ALL"):
                items = extract_sp3m3_night(wb)
                prod_date = target_file_date - timedelta(days=1)
                run_session_line(page, wb, "SP3M3", items, prod_date, args.dry_run)
            if args.line in ("SD9A01","ALL"):
                items = extract_outer_d1(wb, "SD9M01")
                prod_date = target_file_date
                run_session_line(page, wb, "SD9A01", items, prod_date, args.dry_run)
        else:  # morning
            # SP3M3 주간: ERP 생산일 = 파일명 날짜 (당일, 어제 저녁 저장된 파일)
            prod_date = target_file_date
            if args.line in ("SP3M3","ALL"):
                items = extract_sp3m3_day(wb, DAY_CUT_THRESHOLD)
                run_session_line(page, wb, "SP3M3", items, prod_date, args.dry_run)
            if args.line == "SD9A01":
                print("[morning] SD9A01은 저녁 세션 전용 — 스킵")

        print("=== /d0-plan 완료 ===")


if __name__ == "__main__":
    main()
