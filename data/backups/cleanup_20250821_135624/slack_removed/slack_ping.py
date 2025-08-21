# [ACTIVE] VELOS Slack 핑 시스템 - Slack 연결 테스트 스크립트
import json
import os
import urllib.request

tok = os.getenv("SLACK_BOT_TOKEN")
ch = os.getenv("SLACK_CHANNEL") or os.getenv("SLACK_DEFAULT_CHANNEL")

if not tok or not ch:
    raise SystemExit("SLACK_BOT_TOKEN 또는 채널이 없음")

payload = {"channel": ch, "text": "VELOS 한국어 점검: 한글 OK ✅"}

req = urllib.request.Request(
    "https://slack.com/api/chat.postMessage",
    data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
    headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=utf-8"},
)

print(urllib.request.urlopen(req).read().decode("utf-8"))
