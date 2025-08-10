# =============================================
# VELOS: Slack Client
# =============================================
from __future__ import annotations
import os, json, requests

SLACK_API = "https://slack.com/api/chat.postMessage"

class SlackClient:
    def __init__(self):
        self.token = os.environ.get("SLACK_BOT_TOKEN", "").strip()
        if not self.token:
            raise RuntimeError("SLACK_BOT_TOKEN 미설정")

    def send_message(self, channel: str, text: str):
        ch = channel or os.environ.get("SLACK_CHANNEL_ID") or "#general"
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json; charset=utf-8"}
        payload = {"channel": ch, "text": text}
        r = requests.post(SLACK_API, headers=headers, data=json.dumps(payload))
        if not r.ok or not r.json().get("ok"):
            raise RuntimeError(f"Slack 전송 실패: {r.text}")
        return True
