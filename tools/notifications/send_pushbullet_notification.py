# send_pushbullet_notification.py - Pushbullet 모바일 알림 전송

import requests
import os

def send_pushbullet_notification(title, body):
    """
    Pushbullet을 통해 알림 전송
    """
    api_key = os.getenv("PUSHBULLET_API_KEY")
    if not api_key:
        print("❌ PUSHBULLET_API_KEY가 설정되지 않았습니다.")
        return

    headers = {
        "Access-Token": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "type": "note",
        "title": title,
        "body": body
    }

    response = requests.post("https://api.pushbullet.com/v2/pushes", json=data, headers=headers)

    if response.status_code == 200:
        print("✅ Pushbullet 알림 전송 성공")
    else:
        print(f"❌ 전송 실패: {response.status_code} - {response.text}")
