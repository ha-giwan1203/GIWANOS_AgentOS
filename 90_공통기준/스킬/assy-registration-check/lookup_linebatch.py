"""
ERP 라인배치 관리 화면 자동조회 — 모품번 → 컬러 list 추출.

iframe URL: /partLineBatchMng/viewPartLineBatchMng.do
검색 패턴 (line-batch-mainsub MANUAL 기반):
- 입력: document.getElementById('searchProdNo')
- 검색: button text "검색"
- 결과: jQuery('#grid_body').pqGrid('option','dataModel').data

사용:
    from lookup_linebatch import lookup_colors_via_linebatch
    result = lookup_colors_via_linebatch(['89880CV500', ...])
    # {모품번: [{PROD_NO, REV, CAR_KIND, ...}, ...]}

전제: 사용자가 ERP 라인배치 관리 화면을 한 번 직접 진입해서 iframe 활성화한 상태
(layout.do 메뉴 클릭으로 viewPartLineBatchMng.do iframe 로드).
미진입 시 자동 메뉴 클릭 시도.
"""
import json
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

import websocket

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "gerp-unregistered-check"))
import erp_lookup  # CDP/OAuth 공통 자산 재사용


LINEBATCH_IFRAME_PATTERN = "viewPartLineBatchMng.do"
LINEBATCH_MENU_ID = None  # 메뉴 ID 모름 — URL goto 또는 사용자 직접 진입


def _try_open_linebatch_iframe():
    """라인배치 관리 iframe 자동 진입. 메뉴 ID 모르면 URL goto fallback."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(erp_lookup.CDP_URL)
        ctx = browser.contexts[0]
        page = None
        for pg in ctx.pages:
            if 'erp-dev' in pg.url and 'auth-dev' not in pg.url:
                page = pg; break
        if page is None:
            print("[phase1] ERP 탭 없음")
            return False
        already = page.evaluate(f'''
            () => Array.from(document.querySelectorAll('iframe'))
                .some(f => f.src.includes('{LINEBATCH_IFRAME_PATTERN}'))
        ''')
        if already:
            print("[phase1] 라인배치 iframe 이미 진입됨")
            return True

        # URL goto fallback — layout.do 진입 후 사용자 클릭 또는 직접 navigate
        if 'layout.do' not in page.url:
            page.goto("http://erp-dev.samsong.com:19100/layout/layout.do", timeout=30000)
            time.sleep(3)

        # iframe 없으면 사용자 직접 클릭 안내
        print("[phase1] 라인배치 iframe 미진입 — 사용자가 ERP에서 '생산관리 > 기준정보 > 라인배치 관리' 메뉴 직접 클릭 필요")
        return False


def _connect_linebatch_iframe():
    """ERP 탭 WS + 라인배치 iframe context_id 자동 탐지."""
    tabs = json.loads(urllib.request.urlopen(f"{erp_lookup.CDP_URL}/json/list").read())
    erp_tab = None
    for t in tabs:
        url = t.get('url', '')
        if 'erp-dev' in url and 'auth-dev' not in url and t.get('type') == 'page':
            erp_tab = t; break
    if erp_tab is None:
        raise RuntimeError("ERP 탭 없음")

    ws = websocket.create_connection(erp_tab['webSocketDebuggerUrl'],
                                     timeout=30, suppress_origin=True)
    ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
    ws.send(json.dumps({'id': 2, 'method': 'Page.enable'}))

    contexts = {}
    deadline = time.time() + 5
    while time.time() < deadline:
        ws.settimeout(1.0)
        try:
            msg = json.loads(ws.recv())
            if msg.get('method') == 'Runtime.executionContextCreated':
                c = msg['params']['context']
                contexts[c['id']] = {'origin': c.get('origin',''),
                                     'frameId': c.get('auxData',{}).get('frameId','')}
        except Exception:
            break
    ws.settimeout(30)

    # frame tree로 라인배치 frameId 찾기
    ws.send(json.dumps({'id': 60, 'method': 'Page.getFrameTree'}))
    target_fid = None
    deadline = time.time() + 3
    while time.time() < deadline:
        ws.settimeout(1.0)
        try:
            msg = json.loads(ws.recv())
            if msg.get('id') == 60:
                def find(node):
                    f = node.get('frame', {})
                    if LINEBATCH_IFRAME_PATTERN in f.get('url',''):
                        return f.get('id')
                    for child in node.get('childFrames', []):
                        r = find(child)
                        if r: return r
                    return None
                target_fid = find(msg.get('result',{}).get('frameTree',{}))
                break
        except Exception:
            break
    ws.settimeout(30)

    # 같은 frameId에 여러 context (main world + isolated) — jQuery 있는 main world만 선택
    def _has_jquery(cid):
        ws.send(json.dumps({'id': 200 + cid, 'method': 'Runtime.evaluate',
                            'params': {'expression': "typeof jQuery !== 'undefined'",
                                       'contextId': cid, 'returnByValue': True}}))
        try:
            r = json.loads(ws.recv()).get('result', {}).get('result', {})
            return r.get('value') is True
        except Exception:
            return False

    if target_fid:
        # frameId 매칭 context 중 jQuery 있는 것 우선
        candidates = [cid for cid, info in contexts.items() if info.get('frameId') == target_fid]
        for cid in sorted(candidates):
            if _has_jquery(cid):
                print(f"[CDP] 라인배치 context (jQuery main world): id={cid}")
                return ws, cid
        # fallback — 첫 candidate
        if candidates:
            cid = sorted(candidates)[0]
            print(f"[CDP] 라인배치 context (fallback, jQuery 미확인): id={cid}")
            return ws, cid
    raise RuntimeError("라인배치 iframe context 못 찾음 — 사용자가 화면 진입 필요")


def _cdp_eval(ws, js, msg_id=1, ctx_id=17):
    ws.send(json.dumps({'id': msg_id, 'method': 'Runtime.evaluate',
                        'params': {'expression': js, 'contextId': ctx_id, 'returnByValue': True, 'awaitPromise': True}}))
    resp = json.loads(ws.recv())
    r = resp.get('result',{}).get('result',{})
    if r.get('type') == 'string':
        return r['value']
    return json.dumps(r.get('value',''))


def search_linebatch(ws, prod_no, ctx_id):
    """라인배치 화면에서 prod_no 검색 → 상단 grid data 반환."""
    js = f'''
(async () => {{
    const inp = document.getElementById('searchProdNo');
    if (!inp) return JSON.stringify({{error: 'INPUT없음'}});
    inp.focus(); inp.value = ''; inp.value = {json.dumps(prod_no)};
    inp.dispatchEvent(new Event('input', {{bubbles: true}}));
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === '검색');
    if (!btn) return JSON.stringify({{error: '검색버튼없음'}});
    btn.click();
    await new Promise(r => setTimeout(r, 2500));
    try {{
        const data = jQuery('#grid_body').pqGrid('option','dataModel').data;
        return JSON.stringify({{rows: data || []}});
    }} catch (e) {{
        return JSON.stringify({{error: 'grid_read_fail: ' + e.message}});
    }}
}})()
'''
    result_str = _cdp_eval(ws, js, msg_id=4000, ctx_id=ctx_id)
    try:
        return json.loads(result_str)
    except Exception:
        return {"error": "parse_fail", "raw": result_str[:200]}


def lookup_colors_via_linebatch(pns):
    """모품번 list → {pn: [grid_row, ...]}."""
    print(f"=== ERP 라인배치 자동조회 ({len(pns)} 모품번) ===")
    erp_lookup.ensure_chrome_cdp()
    try:
        erp_lookup.ensure_erp_login_via_playwright()
    except Exception as e:
        print(f"[phase0] OAuth 처리: {e}")
    _try_open_linebatch_iframe()
    ws, ctx_id = _connect_linebatch_iframe()

    result = {}
    for i, pn in enumerate(pns):
        erp_lookup.wait_sync_clear()
        r = search_linebatch(ws, pn, ctx_id)
        result[pn] = r.get('rows', []) if 'rows' in r else []
        if 'error' in r:
            print(f"  [{i+1}/{len(pns)}] {pn}: ERROR {r['error']}")
        elif (i+1) % 5 == 0 or (i+1) == len(pns):
            print(f"  [{i+1}/{len(pns)}] {pn}: rows={len(result[pn])}")
        time.sleep(0.5)

    try:
        ws.close()
    except Exception:
        pass
    return result


if __name__ == "__main__":
    test = ["89880CV500"]
    r = lookup_colors_via_linebatch(test)
    print(json.dumps(r, ensure_ascii=False, indent=2)[:2000])
