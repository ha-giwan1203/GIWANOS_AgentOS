# [ACTIVE] scripts/dispatch_slack.py
from __future__ import annotations
import os, json, time
from pathlib import Path

# --- 환경변수 로딩 ---
try:
    from env_loader import load_env
    load_env()
except ImportError:
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
SLACK_WEBHOOK_URL = _env("SLACK_WEBHOOK_URL")
SLACK_BOT_TOKEN = _env("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = _env("SLACK_CHANNEL_ID") or _env("SLACK_CHANNEL")

def send_slack_only(pdf_path: Path, text: str) -> dict:
    """Slack API 방식 전송 함수"""
    if not _env("DISPATCH_SLACK", "1") == "1":
        return {"ok": False, "detail": "disabled", "ts": int(time.time())}

    # Bot Token 방식 우선 사용
    token = SLACK_BOT_TOKEN
    channel = SLACK_CHANNEL_ID
    if not (token and channel):
        return {"ok": False, "detail": "missing SLACK_BOT_TOKEN or SLACK_CHANNEL_ID", "ts": int(time.time())}
    if requests is None:
        return {"ok": False, "detail": "requests not installed", "ts": int(time.time())}

    try:
        # Slack API로 메시지 전송
        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "channel": channel,
                "text": f"{text}\n파일: {pdf_path.name}",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*VELOS Report*\n{text}\n파일: `{pdf_path.name}`"
                        }
                    },
                    {
                        "type": "divider"
                    }
                ]
            },
            timeout=20
        )
        
        resp_data = resp.json()
        return {"ok": bool(resp_data.get("ok")), "detail": f"API: {resp_data.get('error', 'success')}", "ts": int(time.time())}
    except Exception as e:
        return {"ok": False, "detail": f"exception: {e}", "ts": int(time.time())}

def dispatch_slack():
    """Slack 디스패치 메인 함수"""
    # 테스트 보고서 우선 사용
    latest = max(AUTO.glob("velos_test_report_*.pdf"), default=None)
    if not latest:
        # 기존 보고서 사용
        latest = max(AUTO.glob("velos_auto_report_*_ko.pdf"), default=None)
        if not latest:
            print("no pdf found in", AUTO)
            return False

    text = f"VELOS Test Report\nFile: {latest.name}"
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

