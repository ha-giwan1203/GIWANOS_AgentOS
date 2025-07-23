import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)


import os
import json
import requests

webhook_url = os.getenv("SLACK_WEBHOOK_URL")

if not webhook_url:
    print("❌ SLACK_WEBHOOK_URL 환경변수 없음")
else:
    payload = {"text": "✅ GIWANOS 시스템 - Slack Webhook 테스트 메시지"}
    res = requests.post(webhook_url, json=payload)
    if res.status_code == 200:
        print("✅ Slack Webhook 작동 확인됨")
    else:
        print(f"❌ Slack 전송 실패: 상태코드 {res.status_code}")
