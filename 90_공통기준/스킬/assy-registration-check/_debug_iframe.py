"""디버그 — 라인배치 iframe 안에 어떤 sub-frame 있는지 + jQuery 위치."""
import json, sys, time, urllib.request
from pathlib import Path
import websocket
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "gerp-unregistered-check"))
import erp_lookup

tabs = json.loads(urllib.request.urlopen(f"{erp_lookup.CDP_URL}/json/list").read())
erp_tab = next((t for t in tabs if 'erp-dev' in t.get('url','') and 'auth-dev' not in t.get('url','') and t.get('type')=='page'), None)
print(f"탭: {erp_tab.get('url')}")
ws = websocket.create_connection(erp_tab['webSocketDebuggerUrl'], timeout=30, suppress_origin=True)
ws.send(json.dumps({'id':1,'method':'Runtime.enable'}))
ws.send(json.dumps({'id':2,'method':'Page.enable'}))

# 모든 context 수집
contexts = {}
deadline = time.time() + 5
while time.time() < deadline:
    ws.settimeout(1.0)
    try:
        msg = json.loads(ws.recv())
        if msg.get('method') == 'Runtime.executionContextCreated':
            c = msg['params']['context']
            contexts[c['id']] = {'origin': c.get('origin',''),
                                 'frameId': c.get('auxData',{}).get('frameId',''),
                                 'name': c.get('name','')}
    except Exception:
        break
ws.settimeout(30)

# Frame tree
ws.send(json.dumps({'id':50,'method':'Page.getFrameTree'}))
frame_url_by_id = {}
def collect(node):
    f = node.get('frame',{})
    frame_url_by_id[f.get('id')] = f.get('url','')
    for ch in node.get('childFrames', []):
        collect(ch)
deadline = time.time() + 3
while time.time() < deadline:
    ws.settimeout(1.0)
    try:
        msg = json.loads(ws.recv())
        if msg.get('id') == 50:
            collect(msg.get('result',{}).get('frameTree',{}))
            break
    except Exception:
        break
ws.settimeout(30)

print("\nFrame tree:")
for fid, url in frame_url_by_id.items():
    print(f"  frame={fid[:12]}... url={url[:120]}")

# 각 context에서 jQuery 확인
def has_jquery(ws, ctx_id, msg_id):
    js = "(typeof jQuery !== 'undefined') + '|' + (typeof $ !== 'undefined')"
    ws.send(json.dumps({'id':msg_id,'method':'Runtime.evaluate',
                        'params':{'expression':js,'contextId':ctx_id,'returnByValue':True}}))
    try:
        resp = json.loads(ws.recv())
        r = resp.get('result',{}).get('result',{})
        return r.get('value','?')
    except Exception as e:
        return f"err:{e}"

print("\nContext별 jQuery 존재:")
for cid, info in sorted(contexts.items()):
    fid = info.get('frameId','')
    url = frame_url_by_id.get(fid, '(unknown)')
    if not url: continue
    has = has_jquery(ws, cid, 1000+cid)
    if 'linebatch' in url.lower() or 'partlinebatch' in url.lower() or has != 'false|false':
        print(f"  ctx={cid} frame={fid[:12]}... url={url[:100]} jQuery={has}")

ws.close()
