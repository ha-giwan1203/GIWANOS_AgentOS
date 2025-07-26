import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import os
import requests

def send_slack_message(message: str):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL") or os.getenv("SLACK_WEBHOOK")
    if not webhook_url:
        print("❌ 슬랙 웹훅 설정 없음")
        return
    payload = {"text": message}
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            print("✅ Slack 전송 성공")
        else:
            print(f"❌ Slack 전송 실패: 상태코드 {response.status_code}")
    except Exception as e:
        print(f"❌ Slack 전송 중 오류: {e}")
