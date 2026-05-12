"""
GERP 조립비 현황관리 자동 진입 + 라인별 등록 현황 일괄 수집.

흐름:
1. d0-production-plan과 동일 chrome user_data_dir 공유 (CDP 9224, password manager 자격증명 cached)
2. ensure_erp_login (자동 OAuth — input userId 클릭 → arrow down → enter → submit)
3. 조립비 현황관리(New) 화면 진입 (Hdr/Dtl API 호출)
4. 입력된 품번 리스트별 라인 등록 현황 수집 → JSON 반환

기반: 05_생산실적/조립비정산/03_정산자동화/extract_erp_assy_data.py
참조: 90_공통기준/스킬/d0-production-plan/run.py (ensure_chrome_cdp / ensure_erp_login)

매시 5구간(x0:10~13, x0:20~23, ..., x0:50~53) 자동 대기 (waitSyncClear).

사용:
    from erp_lookup import lookup_pns_lines
    result = lookup_pns_lines(pns=["89870BS500OVS", ...], appl_da="2026-04-30", cmpy_cd="0109")
    # result = {pn: [{"ASSY_LINE_CD": "SD9A01", "ASSY_CMPY_CD": "0109", ...}, ...]}
"""
import json
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

import websocket  # pip install websocket-client

# ============================================================
# 설정 — d0-production-plan과 user_data_dir 공유 (자격증명 재사용)
# 단 CDP 포트는 분리 (9224) — d0 9223과 충돌 회피
# ============================================================
CDP_PORT = 9224
CDP_URL = f"http://localhost:{CDP_PORT}"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CHROME_PROFILE = r"C:\Users\User\.flow-chrome-debug"  # d0와 공유 (password 재사용)
ERP_LAYOUT = "http://erp-dev.samsong.com:19100/layout/layout.do"

CONTEXT_ID_DEFAULT = 17  # ERP iframe (extract_erp_assy_data.py 기준)
DELAY_SEC = 0.4
PAGE_SIZE = 10


# ============================================================
# 시간 금지구간 회피 (라인배치 패턴)
# ============================================================
def is_blackout_window() -> bool:
    """매시 x0:10~13 / 20~23 / 30~33 / 40~43 / 50~53 동기화 금지구간."""
    minute = datetime.now().minute % 10
    return minute <= 3 and minute != 0  # x0:10~13 등 (정시 :00~03 제외 — 라인배치 지침 권위)


def wait_sync_clear():
    """금지구간이면 빠져나갈 때까지 대기."""
    while is_blackout_window():
        now = datetime.now()
        nxt = (now.minute // 10 + 1) * 10
        wait_sec = max(1, (nxt - now.minute) * 60 - now.second)
        if wait_sec > 60:
            wait_sec = 60
        print(f"  [동기화 금지] {now.strftime('%H:%M:%S')} 대기 {wait_sec}s")
        time.sleep(wait_sec)


# ============================================================
# Chrome CDP 기동 (d0 패턴)
# ============================================================
def ensure_chrome_cdp():
    """CDP 9224 기동 확인. 없으면 chrome 띄움."""
    try:
        urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=3)
        print(f"[phase0] CDP {CDP_PORT} alive")
        return True
    except Exception:
        pass

    print(f"[phase0] CDP dead — launching Chrome (port={CDP_PORT})")
    _suppress_chrome_crash_restore(CHROME_PROFILE)

    subprocess.Popen([
        CHROME_PATH,
        f"--remote-debugging-port={CDP_PORT}",
        "--remote-debugging-address=127.0.0.1",
        f"--user-data-dir={CHROME_PROFILE}",
        "--no-first-run", "--no-default-browser-check",
        "--disable-session-crashed-bubble",
        "--hide-crash-restore-bubble",
        ERP_LAYOUT,
    ])
    for i in range(15):
        time.sleep(1.5)
        try:
            urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=2)
            print(f"[phase0] CDP up (try={i+1})")
            return True
        except Exception:
            continue
    raise RuntimeError(f"CDP {CDP_PORT} 기동 실패")


def _suppress_chrome_crash_restore(profile_dir: str):
    """비정상 종료 잔재 정리 (d0 패턴)."""
    prefs_path = Path(profile_dir) / "Default" / "Preferences"
    if not prefs_path.exists():
        return
    try:
        data = json.loads(prefs_path.read_text(encoding="utf-8"))
        prof = data.setdefault("profile", {})
        prof["exit_type"] = "Normal"
        prof["exited_cleanly"] = True
        prefs_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"[phase0] Preferences 정리 실패 (무시): {e}")


# ============================================================
# OAuth 자동 로그인 (세션153 — d0 패치 동기화: page.fill DOM 직접 입력)
# ============================================================
def ensure_erp_login_via_playwright():
    """playwright로 OAuth 자동 로그인 처리.

    세션153 (2026-05-13): pyautogui click/down/return 폐기 — OS focus 가로채기 위험 0%.
    ID/PW는 d0-production-plan/.oauth.json에서 로드 (d0 _load_oauth_cred 재사용).
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError("playwright 미설치 — pip install playwright + playwright install chromium")

    # d0의 _load_oauth_cred 재사용 (auth_extract.py와 동일 import 패턴)
    import sys
    from pathlib import Path
    D0_DIR = Path(__file__).resolve().parent.parent / "d0-production-plan"
    if str(D0_DIR) not in sys.path:
        sys.path.insert(0, str(D0_DIR))
    from run import _load_oauth_cred  # noqa

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        ctx = browser.contexts[0]

        # ERP iframe 또는 layout 페이지 찾기
        page = None
        for pg in ctx.pages:
            if "erp-dev.samsong.com" in pg.url or "auth-dev.samsong.com" in pg.url:
                page = pg
                break
        if page is None:
            for pg in ctx.pages:
                if pg.url.startswith("http"):
                    page = pg
                    break
        if page is None:
            raise RuntimeError("사용 가능한 탭 없음")

        page.bring_to_front()
        time.sleep(1.0)

        # 로그인 페이지면 자동 로그인 (DOM 직접 입력)
        if "auth-dev.samsong.com" in page.url and "/login" in page.url:
            print("[phase0] OAuth 로그인 수행 (DOM 직접 입력)")
            user_id, password = _load_oauth_cred()
            page.wait_for_selector('#userId', timeout=10000)
            page.fill('#userId', user_id)
            page.fill('#password', password)
            page.click('#loginBtn')
            time.sleep(3)
            if "/login?error" in page.url:
                print(f"[phase0] ⚠ submit 직후 /login?error — .oauth.json id/pw 검증 필요. URL: {page.url}")

        # OAuth 완료 대기
        deadline = time.time() + 60
        while time.time() < deadline:
            url = page.url
            if ("erp-dev.samsong.com" in url
                    and "auth-dev" not in url
                    and "oauth2/sso" not in url
                    and "/login" not in url):
                break
            time.sleep(0.5)
        else:
            # OAuth 콜백 정체 시 layout.do 직접 이동
            print(f"[phase0] OAuth 정체 — layout.do 직접 이동")
            page.goto(ERP_LAYOUT, timeout=30000)
            time.sleep(5)

        try:
            page.wait_for_load_state("domcontentloaded", timeout=15000)
        except Exception:
            pass
        print(f"[phase0] ERP 진입 완료 — {page.url}")
        return True


# ============================================================
# 조립비 현황관리 iframe 진입 + API 호출
# ============================================================
ASSY_IFRAME_URL_PATTERN = "viewListCmAssyStatusMngNew.do"
ASSY_MENU_ID = "menu_1000003661"  # 조립비 현황관리(New)


def _try_open_assy_menu():
    """조립비 현황관리(New) iframe 자동 진입 — layout.do + 메뉴 a.click().

    ERP가 직접 URL navigate(viewList...) 시 권한 검증으로 403 반환.
    메뉴 클릭 경로(a.click → ERP 메뉴 핸들러)만 권한 통과.
    iframe src 패턴: /cmAssycostMngNew/viewListCmAssyStatusMngNew.do
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[WARN] playwright 미설치")
        return False

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        ctx = browser.contexts[0]
        page = None
        for pg in ctx.pages:
            if 'erp-dev' in pg.url and 'auth-dev' not in pg.url:
                page = pg
                break
        if page is None:
            print("[phase1] ERP 탭 없음")
            return False

        # 이미 조립비 iframe 떠있는지 체크
        already = page.evaluate(f'''
            () => Array.from(document.querySelectorAll('iframe'))
                .some(f => f.src.includes('{ASSY_IFRAME_URL_PATTERN}'))
        ''')
        if already:
            print("[phase1] 조립비 현황관리 iframe 이미 진입됨")
            return True

        # layout.do로 가서 메뉴 클릭
        if 'layout.do' not in page.url:
            page.goto("http://erp-dev.samsong.com:19100/layout/layout.do", timeout=30000)
            time.sleep(3)

        page.bring_to_front()
        result = page.evaluate(f'''
            () => {{
                const a = document.getElementById('{ASSY_MENU_ID}');
                if (!a) return 'menu_not_found';
                a.click();
                return 'clicked';
            }}
        ''')
        if result != 'clicked':
            print(f"[phase1] 메뉴 클릭 실패: {result}")
            return False

        # iframe 진입 확인 (5초 polling)
        for _ in range(10):
            time.sleep(0.5)
            ok = page.evaluate(f'''
                () => Array.from(document.querySelectorAll('iframe'))
                    .some(f => f.src.includes('{ASSY_IFRAME_URL_PATTERN}'))
            ''')
            if ok:
                print(f"[phase1] 조립비 현황관리 iframe 진입 OK")
                return True
        print(f"[phase1] iframe 진입 timeout")
        return False


def _connect_assy_iframe():
    """ERP layout 탭 발견 + iframe context_id 자동 탐지 (Page.getFrameTree)."""
    tabs = json.loads(urllib.request.urlopen(f"{CDP_URL}/json/list").read())
    erp_tab = None
    for t in tabs:
        url = t.get('url', '')
        if 'erp-dev' in url and 'auth-dev' not in url and t.get('type') == 'page':
            erp_tab = t
            break
    if erp_tab is None:
        raise RuntimeError("ERP 탭 없음 — 자동 진입 실패")

    ws = websocket.create_connection(erp_tab['webSocketDebuggerUrl'],
                                     timeout=30, suppress_origin=True)

    # Runtime.enable + Page.enable로 contextCreated 이벤트 수신
    ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
    ws.send(json.dumps({'id': 2, 'method': 'Page.enable'}))

    # contextCreated 이벤트 수집 (시간 제한)
    contexts = {}
    deadline = time.time() + 5
    while time.time() < deadline:
        ws.settimeout(1.0)
        try:
            msg = json.loads(ws.recv())
            if msg.get('method') == 'Runtime.executionContextCreated':
                ctx = msg['params']['context']
                ctx_id = ctx['id']
                origin = ctx.get('origin', '')
                aux = ctx.get('auxData', {})
                frame_id = aux.get('frameId', '')
                contexts[ctx_id] = {'origin': origin, 'frameId': frame_id, 'name': ctx.get('name', '')}
        except websocket.WebSocketTimeoutException:
            break
        except Exception:
            break
    ws.settimeout(30)

    # 1순위: cmAssycostMngNew iframe context 매칭 (frameId → src 매핑 필요)
    # frame tree에서 viewListCmAssyStatusMngNew.do iframe의 frameId 찾기
    ws.send(json.dumps({'id': 60, 'method': 'Page.getFrameTree'}))
    target_frame_id = None
    deadline = time.time() + 3
    while time.time() < deadline:
        ws.settimeout(1.0)
        try:
            msg = json.loads(ws.recv())
            if msg.get('id') == 60:
                tree = msg.get('result', {}).get('frameTree', {})
                # 재귀 탐색
                def find_frame(node):
                    f = node.get('frame', {})
                    if ASSY_IFRAME_URL_PATTERN in f.get('url', ''):
                        return f.get('id')
                    for child in node.get('childFrames', []):
                        r = find_frame(child)
                        if r:
                            return r
                    return None
                target_frame_id = find_frame(tree)
                break
        except websocket.WebSocketTimeoutException:
            break
        except Exception:
            break
    ws.settimeout(30)

    if target_frame_id:
        for cid, info in contexts.items():
            if info.get('frameId') == target_frame_id:
                print(f"[CDP] context auto-detect (frame match): id={cid}")
                return ws, cid

    # 2순위: 가장 최근 erp-dev context
    erp_ctxs = [(c, i) for c, i in contexts.items() if 'erp-dev' in i.get('origin', '')]
    if erp_ctxs:
        cid = sorted(erp_ctxs, key=lambda x: x[0])[-1][0]
        print(f"[CDP] context fallback (latest erp-dev): id={cid}")
        return ws, cid

    print(f"[CDP] context 자동탐지 실패 — fallback id={CONTEXT_ID_DEFAULT}")
    return ws, CONTEXT_ID_DEFAULT


def _cdp_eval(ws, js_code, msg_id=1, context_id=CONTEXT_ID_DEFAULT):
    """CDP Runtime.evaluate."""
    ws.send(json.dumps({
        'id': msg_id,
        'method': 'Runtime.evaluate',
        'params': {
            'expression': js_code,
            'contextId': context_id,
            'returnByValue': True
        }
    }))
    resp = json.loads(ws.recv())
    result = resp.get('result', {}).get('result', {})
    if result.get('type') == 'string':
        return result['value']
    return json.dumps(result.get('value', ''))


def _detect_iframe_context(ws):
    """iframe context_id 자동 탐지 — Page.getFrameTree."""
    ws.send(json.dumps({'id': 50, 'method': 'Page.getFrameTree'}))
    resp = json.loads(ws.recv())
    # frame tree 순회는 복잡 — 일단 기본값 17 사용. 실패 시 수동 변경
    return CONTEXT_ID_DEFAULT


def fetch_pn_lines(ws, prod_no, appl_da, msg_id=1, context_id=CONTEXT_ID_DEFAULT):
    """품번별 라인 등록 현황 (Dtl API) 수집."""
    js = f'''
(function(){{
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/cmAssycostMngNew/selectListCmAssyStatusMngDtlNew.do?searchProdNo={prod_no}&allFlag=N&searchApplDa={appl_da}', false);
    xhr.send();
    if(xhr.status !== 200) return JSON.stringify({{error: xhr.status}});
    var r = JSON.parse(xhr.responseText);
    if(r.statusCode != 200) return JSON.stringify({{error: r.statusCode}});
    return JSON.stringify(r.data.list || []);
}})()
'''
    result_str = _cdp_eval(ws, js, msg_id=msg_id, context_id=context_id)
    try:
        result = json.loads(result_str)
    except Exception:
        return None
    if isinstance(result, dict) and 'error' in result:
        return None
    return result


def fetch_pn_hdr(ws, prod_no, appl_da, cmpy_cd="", msg_id=1, context_id=CONTEXT_ID_DEFAULT):
    """완성품 품번 Hdr API 호출 — 사용자 ERP 검색 절차 그대로 재현.

    사용자 ERP 검색 (조립비 현황관리 화면):
    - 좌측 검색창: 제품번호 입력 / 조립업체 빈칸 / 상태 전체 / 적용일 default
    - 검색 → 우측 상단 그리드에 결과
    - 그래서 cmpy_cd default="" (조립업체 필터 X)
    - 결과 0건 = 완성품 미등록 / 1+건 = 완성품 등록 OK

    Hdr API: selectListCmAssyStatusMngHdrNew.do
    """
    qs = f'searchProdNo={prod_no}&searchApplDa={appl_da}&pq_curPage=1&pq_rPP=20'
    if cmpy_cd:
        qs += f'&searchCmpyCd={cmpy_cd}'
    js = f'''
(function(){{
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/cmAssycostMngNew/selectListCmAssyStatusMngHdrNew.do?{qs}', false);
    xhr.send();
    if(xhr.status !== 200) return JSON.stringify({{error: xhr.status}});
    var r = JSON.parse(xhr.responseText);
    if(r.statusCode != 200) return JSON.stringify({{error: r.statusCode}});
    return JSON.stringify(r.data.list || []);
}})()
'''
    result_str = _cdp_eval(ws, js, msg_id=msg_id, context_id=context_id)
    try:
        result = json.loads(result_str)
    except Exception:
        return None
    if isinstance(result, dict) and 'error' in result:
        return None
    return result


# ============================================================
# 진입점 — 품번 리스트 입력 → 라인 등록 현황 dict 반환
# ============================================================
def lookup_pns_lines(pns, appl_da, cmpy_cd="0109"):
    """
    Args:
        pns: 품번 리스트
        appl_da: 적용일 (YYYY-MM-DD, 보통 정산 월 마지막 날)
        cmpy_cd: 업체코드 (default 0109)
    Returns:
        {pn: [{"ASSY_LINE_CD": ..., "ASSY_CMPY_CD": ..., "DECIDE_NM": ...}, ...]}
        등록 행 없으면 빈 list
    """
    print(f"=== GERP 라인 등록 현황 일괄 조회 ===")
    print(f"품번 {len(pns)}개 / 적용일 {appl_da} / 업체 {cmpy_cd}")

    # 1. Chrome CDP 기동 (없으면 launch)
    ensure_chrome_cdp()

    # 2. OAuth 자동 로그인 (이미 진입돼 있으면 즉시 패스)
    try:
        ensure_erp_login_via_playwright()
    except Exception as e:
        print(f"[phase0] OAuth 처리 (이미 로그인일 수 있음): {e}")

    # 3. 조립비 현황관리(New) 메뉴 자동 클릭 (layout.do + a.click)
    if not _try_open_assy_menu():
        raise RuntimeError("조립비 현황관리(New) iframe 진입 실패")

    # 4. iframe context_id 자동 탐지 + WS 연결
    ws, ctx_id = _connect_assy_iframe()
    print(f"[CDP] 조립비 현황관리 iframe context_id={ctx_id}")

    result = {}
    errors = []
    for i, pn in enumerate(pns):
        wait_sync_clear()
        try:
            dtl = fetch_pn_lines(ws, pn, appl_da, msg_id=1000 + i, context_id=ctx_id)
            if dtl is None:
                result[pn] = []
                errors.append(pn)
            else:
                result[pn] = dtl
            if (i + 1) % 20 == 0:
                print(f"  [{i+1}/{len(pns)}] {pn} → {len(result[pn])}개 라인")
        except Exception as e:
            print(f"  [{i+1}/{len(pns)}] {pn} → EXCEPTION: {e}")
            errors.append(pn)
            try:
                ws.close()
            except Exception:
                pass
            time.sleep(2)
            ws = _connect_ws()
        time.sleep(DELAY_SEC)

    try:
        ws.close()
    except Exception:
        pass

    print(f"\n[DONE] 수집 {len(result)}건 / 에러 {len(errors)}건")
    if errors:
        print(f"  에러 품번: {errors[:10]}{'...' if len(errors) > 10 else ''}")
    return result


if __name__ == "__main__":
    # 단독 실행 테스트
    test_pns = ["89870BS500OVS"]
    r = lookup_pns_lines(test_pns, appl_da="2026-04-30")
    print(json.dumps(r, ensure_ascii=False, indent=2))
