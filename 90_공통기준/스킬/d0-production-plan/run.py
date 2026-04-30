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
CDP_URL = "http://localhost:9223"
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
def _suppress_chrome_crash_restore(profile_dir: str):
    """Chrome 비정상 종료 후 "페이지 복원" 알림 차단.

    세션110 보강: taskkill로 강제 종료된 Chrome을 다시 launch하면 Preferences의
    exit_type이 "Crashed"로 남아 자동 복원 다이얼로그 표시 → 무인 트리거에서 화면 거슬림.
    Preferences 파일의 exit_type / exited_cleanly 정리로 복원 알림 차단.
    """
    import json as _json
    from pathlib import Path as _Path
    prefs_path = _Path(profile_dir) / "Default" / "Preferences"
    if not prefs_path.exists():
        return
    try:
        data = _json.loads(prefs_path.read_text(encoding="utf-8"))
        prof = data.setdefault("profile", {})
        prof["exit_type"] = "Normal"
        prof["exited_cleanly"] = True
        prefs_path.write_text(_json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"[phase0] Preferences 정리 실패 (무시): {e}")


def ensure_chrome_cdp():
    """CDP 9223 기동 확인."""
    import urllib.request
    try:
        urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=3)
        print("[phase0] CDP 9223 alive")
        return True
    except Exception:
        print("[phase0] CDP dead — launching Chrome")

    # Chrome 비정상 종료 잔재 정리 (세션110 — 복원 알림 차단)
    _suppress_chrome_crash_restore(CHROME_PROFILE)

    subprocess.Popen([
        CHROME_PATH,
        f"--remote-debugging-port=9223",
        f"--remote-debugging-address=127.0.0.1",  # 세션105 — IPv6 기본 바인딩 회피
        f"--user-data-dir={CHROME_PROFILE}",
        "--no-first-run", "--no-default-browser-check",
        "--disable-session-crashed-bubble",  # 세션110 — 복원 다이얼로그 차단
        "--hide-crash-restore-bubble",
        "--no-default-browser-check",
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
    raise RuntimeError("CDP 9223 기동 실패")


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


def _wait_oauth_complete(page, timeout_sec: float = 60.0):
    """OAuth 완료 대기 — auth-dev 떠나고 erp-dev 본 페이지(oauth2/sso 콜백 제외) 도달까지.

    세션110 보강: 기존 `"erp-dev.samsong.com" in url` 조건은 OAuth 콜백 중간 단계
    `oauth2/sso` URL도 매칭되어 잘못 break 발생 → 미완료 상태에서 D0_URL 시도 →
    auth-dev/login 페이지 redirect → btnExcelUpload timeout 실패 시나리오.

    세션131 [E] 보강: default 30→60s. 5일 중 4일 morning 자동화 OAuth timeout 실패
    실측 (4/27 4/29 4/30). 7시 ERP 부하 + cold start fresh launch에서 OAuth 콜백 redirect
    chain이 30s를 넘어가는 케이스 흡수.
    """
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        url = page.url
        if ("erp-dev.samsong.com" in url
                and "auth-dev" not in url
                and "oauth2/sso" not in url
                and "/login" not in url):
            return True
        time.sleep(0.5)
    return False


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

    # OAuth 완료 명시 대기 (세션110 보강 — oauth2/sso 콜백 부분 매칭 버그 수정 / 세션131 [E] 60s 상향)
    if not _wait_oauth_complete(page, timeout_sec=60.0):
        print(f"[phase0] OAuth 완료 대기 60s 실패 — 현재 URL: {page.url}")
        # login 페이지 다시 도달 시 1회 재시도
        if "auth-dev.samsong.com" in page.url and "/login" in page.url:
            print("[phase0] login 페이지 재도달 — 재로그인 1회 시도")
            ensure_erp_login(page)
            if not _wait_oauth_complete(page, timeout_sec=60.0):
                raise RuntimeError(f"OAuth 완료 2회 실패: {page.url}")
        elif "auth-dev.samsong.com" in page.url:
            # 세션124 [3way] 보강: 비login auth-dev 정착(클라이언트 선택 화면 등) 시 D0_URL 직접 이동 1회 시도
            print("[phase0] auth-dev 비login 정착 — D0_URL 직접 이동 1회 시도")
            _safe_goto(page, D0_URL)
            if not _wait_oauth_complete(page, timeout_sec=60.0):
                raise RuntimeError(f"OAuth 완료 실패: auth-dev 클라이언트 선택 화면에서 D0_URL 직접 이동 1회 시도 후에도 erp-dev 미도달 — 현재 URL: {page.url}")
        else:
            # 세션131 [E]: OAuth 콜백 URL(oauth2/sso 등) 정체 — D0_URL 직접 navigate fallback
            # 사용자 실측 관찰(2026-04-30): 로그인 성공 후 생산계획 탭 redirect 못 받고 멍때리다 실패.
            # ERP 서버가 OAuth 콜백 후 redirect 누락 의심. 4/29 auth-dev 비login 분기와 동일 패턴 —
            # 클라이언트가 능동 navigate로 우회. 4/27·4/29·4/30 3건 동일 증상 흡수.
            print(f"[phase0] OAuth 콜백 정체 ({page.url}) — D0_URL 직접 이동 1회 시도")
            _safe_goto(page, D0_URL)
            if not _wait_oauth_complete(page, timeout_sec=60.0):
                raise RuntimeError(f"OAuth 완료 실패 (D0_URL 직접 이동 후에도 미완료): {page.url}")

    try: page.wait_for_load_state("domcontentloaded", timeout=15000)
    except Exception: pass
    time.sleep(2)

    if "viewListDoAddnPrdtPlanInstrMngNew" not in page.url:
        _safe_goto(page, D0_URL)
        try: page.wait_for_load_state("domcontentloaded", timeout=20000)
        except Exception: pass
        time.sleep(3)
    print(f"[phase0] D0 화면 진입: {page.url}")
    return page


def _safe_goto(page, url, max_retries=3):
    """page.goto 실패 시 단계적 재시도 + ERR_BLOCKED_BY_CLIENT 우회.

    1차~N차: page.goto (timeout 30s, 간격 증가)
    최종 fallback: JavaScript window.location.href 설정 (CDP 레벨 차단 우회)
    """
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            page.goto(url, timeout=30000)
            return
        except Exception as e:
            last_err = e
            msg = str(e)
            print(f"[phase0] goto 시도 {attempt}/{max_retries} 실패: {msg[:120]}")
            if "ERR_BLOCKED_BY_CLIENT" in msg and attempt == max_retries:
                # 마지막: JS navigation 우회
                print("[phase0] ERR_BLOCKED_BY_CLIENT 감지 — JS window.location 우회 시도")
                try:
                    page.evaluate(f"() => {{ window.location.href = {url!r}; }}")
                    time.sleep(5)
                    page.wait_for_load_state("domcontentloaded", timeout=20000)
                    if "viewListDoAddnPrdtPlanInstrMngNew" in page.url:
                        print(f"[phase0] JS 우회 성공: {page.url}")
                        return
                except Exception as e2:
                    print(f"[phase0] JS 우회도 실패: {e2}")
            time.sleep(3 * attempt)
    raise RuntimeError(f"goto {url} 실패 (전체 {max_retries}회 + JS 우회): {last_err}")


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
    """출력용 시트 야간 섹션.

    구조:
      R1: `◀ D+1 야간계획`
      R2: 데이터 헤더 (순서/신MES 품번/지시)
      R3~: 실제 데이터
      R?: `◀ D+2 주간계획` (종료 경계)
    """
    ws = wb["출력용"]
    start = 3
    night_end = 34  # 보수적 default
    for r in range(2, ws.max_row+1):
        v = ws.cell(row=r, column=2).value
        if v and "주간계획" in str(v):
            night_end = r - 1
            break
    items = []
    for r in range(start, night_end+1):
        part = ws.cell(row=r, column=9).value
        qty = ws.cell(row=r, column=11).value
        if not (part and qty):
            continue
        try:
            qty_int = int(qty)
        except (ValueError, TypeError):
            continue  # 헤더 행 등 숫자 아닌 값 skip
        items.append({"PROD_NO": str(part).strip(), "QTY": qty_int})
    print(f"[phase1] SP3M3 야간: {len(items)}건")
    return items


def extract_sp3m3_day(wb, cut_threshold=DAY_CUT_THRESHOLD):
    """출력용 시트 주간 섹션 — 누적 ≥ cut_threshold 첫 행까지 포함.

    구조 (2026-04-25 실증):
      R32: `◀ D+2 주간계획` 섹션 헤더
      R33: 데이터 헤더 (순서/신MES 품번/지시)
      R34~: 실제 데이터

    day_start = 주간계획 헤더 r + 2 (데이터 헤더 한 줄 skip).
    방어: 헤더 행이 추가로 있어도 try/except로 숫자 아닌 K값은 skip.
    """
    ws = wb["출력용"]
    day_start = None
    for r in range(2, ws.max_row+1):
        v = ws.cell(row=r, column=2).value
        if v and "주간계획" in str(v):
            day_start = r + 2  # 섹션 헤더 + 데이터 헤더 둘 다 skip
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
        try:
            qty_int = int(qty)
        except (ValueError, TypeError):
            # 헤더 행이 더 있거나 이상값 — skip
            continue
        items.append({"PROD_NO": str(part).strip(), "QTY": qty_int})
        cumsum += qty_int
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
    """ERP 양식을 Excel COM(win32com)으로 편집·저장.

    왜 win32com인가:
      openpyxl이 생성·저장한 xlsx는 ERP 서버 파서(아마 Apache POI 구버전)가
      COL2(제품번호)를 빈값으로 파싱하는 이슈 있음 (2026-04-24 세션104 실증).
      OOXML 내부 구조(shared strings, cell type 속성, 시트 XML 네임스페이스)
      차이 때문이며, Microsoft Excel이 직접 저장한 파일만 서버가 정상 파싱.
      → Excel COM으로 실제 Excel 프로세스가 저장해야 호환.

    흐름:
      1. 템플릿(ERP 양식 또는 SSKR 검증본) 복제
      2. Excel COM 열어 R2~last 데이터 ClearContents
      3. 새 데이터 R2부터 작성
      4. Excel이 Save (Visible=False, DisplayAlerts=False로 조용히)
    """
    import shutil
    template = Path(__file__).parent / "template" / "SSKR_D0_template.xlsx"
    if not template.exists():
        raise FileNotFoundError(f"ERP 양식 템플릿 없음: {template}")
    shutil.copy(template, out_path)

    try:
        import win32com.client
    except ImportError:
        raise RuntimeError("win32com 필요 (pywin32 설치 필요). pip install pywin32")

    xl = win32com.client.Dispatch("Excel.Application")
    xl.Visible = False
    xl.DisplayAlerts = False
    try:
        wb = xl.Workbooks.Open(str(out_path))
        try:
            ws = wb.Worksheets("Sheet1")
        except Exception:
            ws = wb.Worksheets(1)
        # 기존 데이터 clear (헤더 R1 유지)
        last = ws.Cells(ws.Rows.Count, 1).End(-4162).Row  # xlUp
        if last > 1:
            ws.Range(f"A2:C{last}").ClearContents()
        # 새 데이터 R2부터 작성
        date_str = prod_date.strftime("%Y-%m-%d")
        for i, it in enumerate(items, start=2):
            ws.Cells(i, 1).Value = date_str
            ws.Cells(i, 2).Value = it["PROD_NO"]
            ws.Cells(i, 3).Value = it["QTY"]
        wb.Save()
        wb.Close()
    finally:
        xl.Quit()
    print(f"[phase2] 업로드 엑셀 생성: {out_path.name} ({len(items)}건) — Excel COM 저장 (서버 파서 호환)")


# ============================================================
# Phase 3: D0 업로드 (selectList + multiList)
# ============================================================
def _wait_d0_popup_frame(page, timeout_sec: float = 25.0):
    """D0 업로드 팝업 iframe 폴링 (frame URL 매칭 + DOM querySelector 보강).

    iframe[name="ifr_user"]는 즉시 생성되지만 src URL이 about:blank → popupPmD0AddnUpload.do
    로 늦게 set되는 경우가 있어, frame URL 매칭만으로는 놓칠 수 있다 (세션107 실증).
    DOM 직접 조회를 보조 신호로 사용해 frame 객체가 반영될 때까지 추가 대기.
    """
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        for fr in page.frames:
            if "popupPmD0AddnUpload" in fr.url:
                return fr
        try:
            has_iframe = page.evaluate(
                "() => !!document.querySelector('iframe[src*=\"popupPmD0AddnUpload\"]')"
            )
            if has_iframe:
                time.sleep(0.5)
                for fr in page.frames:
                    if "popupPmD0AddnUpload" in fr.url:
                        return fr
        except Exception:
            pass
        time.sleep(0.3)
    return None


def d0_upload(page, xlsx_path: Path, parse_only: bool = False):
    """팝업 오픈 → selectList → multiList.

    parse_only=True: selectList(엑셀 첨부 + 서버 파싱 + 화면 표시)까지만 수행하고 multiList(DB 저장) 스킵.
    검증 모드 전용 (Phase 4/5 미진행)."""
    # 페이지 로드 확인 + 버튼 대기 (세션107 Gemini 지적: 15s → 30s, ERP 초기 로드 지연 대응)
    try:
        page.wait_for_selector("#btnExcelUpload", timeout=30000)
    except Exception:
        print(f"[phase3] #btnExcelUpload 대기 실패 (30s timeout) — 현재 URL: {page.url}")
        raise

    # 팝업 iframe 먼저 검사 (이미 열려있으면 재사용, reload 생략)
    ifr = None
    for fr in page.frames:
        if "popupPmD0AddnUpload" in fr.url:
            ifr = fr; break

    if ifr is not None:
        print(f"[phase3] 기존 팝업 재사용: {ifr.url[:80]}")
    else:
        # 팝업 없음 — overlay 잔재만 있으면 reload 후 재오픈
        has_overlay = page.evaluate("""() => {
            return document.querySelectorAll('.ui-widget-overlay').length > 0
                || Array.from(document.querySelectorAll('.ui-dialog')).some(d => d.offsetParent !== null);
        }""")
        if has_overlay:
            print("[phase3] 팝업 없이 overlay만 잔존 — 페이지 reload")
            try:
                page.reload(timeout=30000, wait_until="domcontentloaded")
                page.wait_for_selector("#btnExcelUpload", timeout=30000)
                time.sleep(3)
            except Exception as e:
                print(f"[phase3] reload err: {e}")
    if ifr is None:
        # 클릭 재시도 (최대 3번) — 폴링은 _wait_d0_popup_frame (25초, DOM 보강)
        for attempt in range(3):
            try:
                page.locator("#btnExcelUpload").first.click()
            except Exception as e:
                print(f"[phase3] 클릭 실패 try={attempt+1}: {e}")
                time.sleep(2)
                continue
            ifr = _wait_d0_popup_frame(page, timeout_sec=25.0)
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
            const to = setTimeout(() => resolve({ok:false, err:'timeout 120s'}), 120000);
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

    if parse_only:
        print("[phase3 parse-only] selectList 완료 — multiList(DB 저장) 스킵 + 팝업 유지 (사용자 확인용)")
        return

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


def dedupe_night_first_5(page, items, check_count=5):
    """야간 추출 결과의 첫 N행(기본 5)을 ERP 상단 grid 기등록분과 비교해 중복 제외.

    매칭 기준: REG_DT=오늘 AND **PROD_NO 일치만** (수량 무관, 2026-04-29 사용자 결정 v3.2).
    매칭된 행만 items에서 제외. N+1번째 이후는 그대로.

    2026-04-29 사용자 요청 — SP3M3 야간 1~5행이 주간 등록분과 2중 등록되는 현상 방지.
    초기 v3.1은 PROD_NO+수량 동시 매칭이었으나, 같은 품번이면 수량 다르더라도 작업자 입장에서
    중복 작업 위험 동일하므로 PROD_NO만으로 매칭하도록 정책 단순화.
    """
    if not items:
        return items
    today_str = datetime.now().strftime("%Y-%m-%d")
    grid = page.evaluate("""(today) => {
        try {
            const d = jQuery('#grid_body').pqGrid('option','dataModel').data;
            return d.filter(r => r.REG_DT === today).map(r => ({
                PROD_NO: r.PROD_NO,
                QTY: Number(r.PRDT_QTY || r.ADD_PRDT_QTY || r.PRDT_PLAN_QTY || 0)
            }));
        } catch(e) { return []; }
    }""", today_str)

    if not grid:
        print(f"[dedupe] 상단 grid REG_DT={today_str} 등록분 0건 — 야간 dedupe 스킵 (전량 진행)")
        return items

    skipped, kept = [], []
    for i, it in enumerate(items):
        if i < check_count:
            # 수량 무관, PROD_NO만 매칭 (v3.2)
            match = next((g for g in grid if g["PROD_NO"] == it["PROD_NO"]), None)
            if match:
                skipped.append(it)
                # 로그에는 야간 qty + 주간 등록 qty 둘 다 표시 (참고용)
                print(f"[dedupe] 야간 {i+1}행 PROD_NO={it['PROD_NO']} 야간qty={it['QTY']} 주간qty={match['QTY']} → 품번 일치, 제외")
                continue
        kept.append(it)
    print(f"[dedupe] 야간 추출 {len(items)}건 → 등록 {len(kept)}건 / 제외 {len(skipped)}건 (1~{check_count}행만 검사, 품번 일치 기준)")
    return kept


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
            const to = setTimeout(() => resolve({ok:false, err:'timeout 120s'}), 120000);
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
def run_session_line(page, wb, line, items, prod_date, dry_run, verify_prod_date=None, parse_only=False):
    if not items:
        print(f"[{line}] 추출 0건 — 스킵")
        return
    cfg = LINE_CONFIG[line]
    xlsx = UPLOAD_DIR / f"d0_{line}_{prod_date.strftime('%Y%m%d')}.xlsx"
    make_upload_xlsx(items, prod_date, xlsx)

    if dry_run:
        print(f"[{line}] dry-run: 엑셀 생성까지만 (추출 {len(items)}건)")
        return

    if parse_only:
        d0_upload(page, xlsx, parse_only=True)
        print(f"[{line}] parse-only: 업로드 창에 엑셀 첨부 + 서버 파싱까지만 (추출 {len(items)}건). Phase 4/5 미진행")
        return

    d0_upload(page, xlsx)
    target_line = "SP3M3" if line == "SP3M3" else "SD9A01"
    batch = rank_batch(page, items, target_line, cfg["save_url"], dry_run=False)
    print(f"[{line}] rank_batch: {batch}")
    if batch["failed"] > 0:
        print(f"[{line}] 실패 존재 — 최종 저장 보류")
        return
    final_save(page, cfg["save_url"])
    verify_smartmes(target_line, verify_prod_date or prod_date, items)


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
    ap.add_argument("--parse-only", action="store_true", help="검증 모드: 엑셀 업로드창 첨부 + 서버 파싱(selectList)까지만. multiList(DB 저장)/Phase 4-5 모두 스킵")
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
            elif args.parse_only:
                d0_upload(page, xlsx_path, parse_only=True)
                print("[direct] parse-only: 엑셀 첨부 + 서버 파싱까지만. Phase 4/5 미진행")
                return
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
                # Phase 1.5: 야간 1~5행 dedupe (주간 등록분과 PROD_NO+수량 일치 시 제외)
                items = dedupe_night_first_5(page, items)
                prod_date = target_file_date - timedelta(days=1)
                run_session_line(page, wb, "SP3M3", items, prod_date, args.dry_run, verify_prod_date=prod_date, parse_only=args.parse_only)
            if args.line in ("SD9A01","ALL"):
                items = extract_outer_d1(wb, "SD9M01")
                prod_date = target_file_date
                run_session_line(page, wb, "SD9A01", items, prod_date, args.dry_run, verify_prod_date=prod_date, parse_only=args.parse_only)
        else:  # morning
            # SP3M3 주간: ERP 생산일 = 파일명 날짜 (당일, 어제 저녁 저장된 파일)
            prod_date = target_file_date
            if args.line in ("SP3M3","ALL"):
                items = extract_sp3m3_day(wb, DAY_CUT_THRESHOLD)
                run_session_line(page, wb, "SP3M3", items, prod_date, args.dry_run, verify_prod_date=prod_date, parse_only=args.parse_only)
            if args.line == "SD9A01":
                print("[morning] SD9A01은 저녁 세션 전용 — 스킵")

        print("=== /d0-plan 완료 ===")


if __name__ == "__main__":
    main()
