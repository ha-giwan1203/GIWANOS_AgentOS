import os
import mimetypes
import json
from pathlib import Path
import requests
from dotenv import load_dotenv

from modules.report_paths import ROOT, P
ENV = ROOT / "configs" / ".env"
if not ENV.exists():
    print(f"[ERROR] .env 없음: {ENV}")
    raise SystemExit(1)
load_dotenv(dotenv_path=ENV)

TOK = os.getenv("SLACK_BOT_TOKEN")
CH = os.getenv("SLACK_CHANNEL_ID") or os.getenv("SLACK_SUMMARY_CH") or os.getenv("SLACK_CHANNEL")
if not TOK or not CH:
    print("[ERROR] SLACK_BOT_TOKEN/채널 누락")
    raise SystemExit(1)

API = "https://slack.com/api"
HDR = {"Authorization": f"Bearer {TOK}"}


def mime(p):
    return mimetypes.guess_type(p.name)[0] or "application/octet-stream"


def make_dummy():
    d = ROOT / "data" / "reports"
    d.mkdir(parents=True, exist_ok=True)
    f = d / "velos_report_latest.pdf"
    # 최소 PDF 시그니처
    f.write_bytes(b"%PDF-1.4\n% VELOS PROBE\n")
    return f


def pjson(r):
    try:
        j = r.json()
    except Exception:
        j = {"status": r.status_code, "raw": r.text[:400]}
    j["_http"] = r.status_code
    return j


def try_legacy(f):
    with open(f, "rb") as fp:
        data = {"channels": CH, "title": f"VELOS Probe - {f.name}"}
        r = requests.post(
            f"{API}/files.upload",
            headers=HDR,
            data=data,
            files={"file": (f.name, fp, mime(f))},
        )
    return (r.status_code == 200 and r.json().get("ok", False)), pjson(r)


def try_upload_v2(f):
    with open(f, "rb") as fp:
        data = {
            "channel_id": CH,
            "filename": f.name,
            "title": f"VELOS Probe - {f.name}",
        }
        r = requests.post(
            f"{API}/files.uploadV2",
            headers=HDR,
            data=data,
            files={"file": (f.name, fp, mime(f))},
        )
    return (r.status_code == 200 and r.json().get("ok", False)), pjson(r)


def try_external_form(f):
    # 1) URL 발급 (form)
    r1 = requests.post(
        f"{API}/files.getUploadURLExternal",
        headers=HDR,
        data={"filename": f.name, "length": str(f.stat().st_size)},
    )
    j1 = pjson(r1)
    if not (r1.status_code == 200 and j1.get("ok")):
        return False, {"where": "getUploadURLExternal(form)", **j1}
    url, fid = j1["upload_url"], j1["file_id"]
    # 2) PUT 업로드
    with open(f, "rb") as fp:
        put = requests.put(url, data=fp, headers={"Content-Type": mime(f)})
    if not (200 <= put.status_code < 300):
        return False, {"where": "PUT(form)", "status": put.status_code}
    # 3) complete (form, files는 JSON 문자열)
    files_field = json.dumps([{"id": fid, "title": f"VELOS Probe - {f.name}"}], ensure_ascii=False)
    r3 = requests.post(
        f"{API}/files.completeUploadExternal",
        headers=HDR,
        data={"files": files_field, "channel_id": CH, "initial_comment": "probe"},
        timeout=15,
    )
    return (r3.status_code == 200 and r3.json().get("ok", False)), pjson(r3)


def try_external_json(f):
    # 1) URL 발급 (JSON)
    payload = {"filename": f.name, "length": f.stat().st_size, "content_type": mime(f)}
    r1 = requests.post(
        f"{API}/files.getUploadURLExternal",
        headers={**HDR, "Content-Type": "application/json;charset=utf-8"},
        json=payload,
        timeout=15,
    )
    j1 = pjson(r1)
    if not (r1.status_code == 200 and j1.get("ok")):
        return False, {"where": "getUploadURLExternal(json)", **j1}
    url, fid = j1["upload_url"], j1["file_id"]
    # 2) PUT 업로드
    with open(f, "rb") as fp:
        put = requests.put(url, data=fp, headers={"Content-Type": mime(f)})
    if not (200 <= put.status_code < 300):
        return False, {"where": "PUT(json)", "status": put.status_code}
    # 3) complete (form)
    files_field = json.dumps([{"id": fid, "title": f"VELOS Probe - {f.name}"}], ensure_ascii=False)
    r3 = requests.post(
        f"{API}/files.completeUploadExternal",
        headers=HDR,
        data={"files": files_field, "channel_id": CH},
        timeout=15,
    )
    return (r3.status_code == 200 and r3.json().get("ok", False)), pjson(r3)


def main():
    f = make_dummy()
    print(f"[INFO] 대상: {f}")
    strategies = [
        ("legacy(files.upload)", try_legacy),
        ("uploadV2", try_upload_v2),
        ("external(form)", try_external_form),
        ("external(json)", try_external_json),
    ]
    success = None
    for name, fn in strategies:
        try:
            ok, info = fn(f)
            tag = "OK" if ok else "FAIL"
            err = info.get("error") if isinstance(info, dict) else info
            print(f"[{tag}] {name} → {err} (http={info.get('_http')})")
            if ok:
                success = name
                break
        except Exception as e:
            print(f"[EXCPT] {name} → {e}")
            continue
    if success:
        print(f"[RESULT] SUCCESS via {success}")
    else:
        print("[RESULT] ALL FAILED")


if __name__ == "__main__":
    main()

