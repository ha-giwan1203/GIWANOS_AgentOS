# slack_api.py - Slack 메시지 전송용 기본 API

import requests
import os

def send_slack_message(channel, message, token=None):
    """
    지정된 Slack 채널에 메시지를 전송합니다.
    """
    token = token or os.getenv("SLACK_BOT_TOKEN")
    if not token:
        raise ValueError("SLACK_BOT_TOKEN이 설정되지 않았습니다.")

    url = "https://slack.com/api/chat.postMessage"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "channel": channel,
        "text": message
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.json()
