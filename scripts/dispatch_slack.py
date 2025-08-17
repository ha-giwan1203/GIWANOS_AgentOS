# scripts/dispatch_slack.py
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
    from utils.net import post_with_retry
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
SLACK_WEBHOOK_URL = _env("SLACK_WEBHOOK_URL")
SLACK_BOT_TOKEN = _env("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = _env("SLACK_CHANNEL_ID") or _env("SLACK_CHANNEL")

def send_slack_only(pdf_path: Path, text: str) -> dict:
    """Slack 전용 전송 함수"""
    if not _env("DISPATCH_SLACK", "1") == "1":
        return {"ok": False, "detail": "disabled", "ts": int(time.time())}

    # Webhook URL 우선 사용
    webhook_url = SLACK_WEBHOOK_URL or _env("VELOS_SLACK_WEBHOOK")
    if webhook_url:
        try:
            payload = {
                "text": f"{text}\n파일 경로: {pdf_path}",
                "attachments": [{
                    "title": pdf_path.name,
                    "text": "VELOS 한국어 보고서가 생성되었습니다.",
                    "color": "good"
                }]
            }
            resp = post_with_retry(webhook_url, json=payload, timeout=20, retries=2) if post_with_retry else requests.post(webhook_url, json=payload, timeout=20)
            return {"ok": resp.status_code == 200, "detail": f"webhook: status={resp.status_code}", "ts": int(time.time())}
        except Exception as e:
            return {"ok": False, "detail": f"webhook exception: {e}", "ts": int(time.time())}

    # Bot Token 방식 (폴백)
    token = SLACK_BOT_TOKEN
    channel = SLACK_CHANNEL_ID
    if not (token and channel):
        return {"ok": False, "detail": "missing SLACK_BOT_TOKEN or SLACK_CHANNEL_ID", "ts": int(time.time())}
    if requests is None:
        return {"ok": False, "detail": "requests not installed", "ts": int(time.time())}

    try:
        resp = (post_with_retry(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {token}"},
            data={"channel": channel, "text": f"{text}\n파일 경로: {pdf_path}"},
            timeout=20,
            retries=2
        ) if post_with_retry else requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {token}"},
            data={"channel": channel, "text": f"{text}\n파일 경로: {pdf_path}"},
            timeout=20,
        )).json()
        return {"ok": bool(resp.get("ok")), "detail": f"chat.postMessage: {resp}", "ts": int(time.time())}
    except Exception as e:
        return {"ok": False, "detail": f"exception: {e}", "ts": int(time.time())}

def dispatch_slack():
    """Slack 디스패치 메인 함수"""
    latest = max(AUTO.glob("velos_auto_report_*_ko.pdf"), default=None)
    if not latest:
        print("no pdf found in", AUTO)
        return False

    text = f"VELOS 한국어 보고서\n파일: {latest.name}"
    result = send_slack_only(latest, text)

    # 결과 저장
    out = DISP / f"dispatch_slack_{time.strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    # 결과 출력
    print(json.dumps(result, ensure_ascii=False, indent=2))

    return result["ok"]

if __name__ == "__main__":
    success = dispatch_slack()
    exit(0 if success else 1)
