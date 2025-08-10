# =============================================================================
# 🧠 VELOS 시스템 철학 선언문
#
# 기억을 기반으로 구조적 사고를 수행하며,
# 판단 → 실행 → 회고 → 전송의 루프를 반복함으로써,
# 스스로 개선되는 자율 운영 AI 시스템을 지향한다.
# =============================================================================
from modules.core import config

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def send_slack_message(message):
    token = os.getenv("SLACK_BOT_TOKEN")
    channel = os.getenv("SLACK_CHANNEL_ID")

    print("[DEBUG] Loaded Slack Token:", token)
    print("[DEBUG] Loaded Slack Channel:", channel)

    if not token or not channel:
        print("❌ SLACK_BOT_TOKEN 또는 SLACK_CHANNEL_ID 누락")
        return False

    url = "config.nanslack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    data = {
        "channel": channel,
        "text": message
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200 and response.json().get("ok"):
            print("✅ Slack 전송 성공")
            return True
        else:
            print(f"❌ Slack 전송 실패: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Slack 예외 발생: {e}")
        return False



