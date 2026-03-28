# [ACTIVE] scripts/dispatch_push.py
from __future__ import annotations
import os, json, time
from pathlib import Path

# --- 환경변수 로딩 ---
def _load_dotenv():
    try:
        from dotenv import load_dotenv
    except Exception:
        return
    root = Path(r"C:\giwanos")
    for p in (root/"configs/.env", root/".env"):
        if p.exists():
            load_dotenv(dotenv_path=p, override=False, encoding="utf-8")
_load_dotenv()

try:
    import requests
    from modules.utils.net import post_with_retry
except Exception:
    requests = None
    post_with_retry = None

ROOT = Path(r"C:\giwanos")
AUTO = ROOT / "data" / "reports" / "auto"
DISP = ROOT / "data" / "reports" / "_dispatch"
DISP.mkdir(parents=True, exist_ok=True)

def _env(name, default=None):
    return os.getenv(name, default)

# 호환 매핑
PUSHBULLET_TOKEN = _env("PUSHBULLET_TOKEN") or _env("PUSHBULLET_API_KEY")

def send_pushbullet_only(title: str, body: str) -> dict:
    """Pushbullet 전용 전송 함수"""
    if not _env("DISPATCH_PUSH", "1") == "1":
        return {"ok": False, "detail": "disabled", "ts": int(time.time())}

    token = PUSHBULLET_TOKEN
    if not token:
        return {"ok": False, "detail": "missing PUSHBULLET_TOKEN", "ts": int(time.time())}
    if requests is None:
        return {"ok": False, "detail": "requests not installed", "ts": int(time.time())}

    try:
        resp = post_with_retry(
            "https://api.pushbullet.com/v2/pushes",
            headers={"Access-Token": token, "Content-Type": "application/json"},
            data=json.dumps({"type":"note","title": title,"body": body}, ensure_ascii=False).encode("utf-8"),
            timeout=20,
            retries=2
        ) if post_with_retry else requests.post(
            "https://api.pushbullet.com/v2/pushes",
            headers={"Access-Token": token, "Content-Type": "application/json"},
            data=json.dumps({"type":"note","title": title,"body": body}, ensure_ascii=False).encode("utf-8"),
            timeout=20
        )
        ok = resp.status_code < 300
        return {"ok": ok, "detail": f"status={resp.status_code}", "ts": int(time.time())}
    except Exception as e:
        return {"ok": False, "detail": f"exception: {e}", "ts": int(time.time())}

def dispatch_pushbullet():
    """Pushbullet 디스패치 메인 함수"""
    latest = max(AUTO.glob("velos_auto_report_*_ko.pdf"), default=None)
    if not latest:
        print("no pdf found in", AUTO)
        return False

    title = "VELOS 한국어 보고서"
    body = f"VELOS 한국어 보고서가 생성되었습니다.\n파일: {latest.name}"
    result = send_pushbullet_only(title, body)

    # 결과 저장
    out = DISP / f"dispatch_pushbullet_{time.strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    # 결과 출력
    print(json.dumps(result, ensure_ascii=False, indent=2))

    return result["ok"]

if __name__ == "__main__":
    success = dispatch_pushbullet()
    exit(0 if success else 1)




