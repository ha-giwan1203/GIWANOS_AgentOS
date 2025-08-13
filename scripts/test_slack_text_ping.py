# ------------------------------------------------------------
# test_slack_text_ping.py
# - chat.postMessage로 채널에 텍스트 전송
# ------------------------------------------------------------
import os
import requests
from pathlib import Path
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

msg = "VELOS ping 테스트: I'm alive ✅"
r = requests.post(
    "https://slack.com/api/chat.postMessage",
    headers={"Authorization": f"Bearer {TOK}"},
    data={"channel": CH, "text": msg},
    timeout=15,
)
print("[API]", r.status_code, r.text[:400])

