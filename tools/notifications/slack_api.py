# =============================================================================
# 🧠 VELOS 시스템 철화 선언문
#
# 기억을 기반으로 구조적 생각을 수행하며,
# 판단 → 실행 → 회고 → 전송의 루프를 반복함으로써,
# 자신의 복구 가능한 자유 운영 AI 시스템을 지향한다.
# =============================================================================

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def send_pushbullet_notification(title, body):
    token = os.getenv("PUSHBULLET_API_KEY")
    print("[DEBUG] Loaded Pushbullet Token:", token)  # ✅ 디버깅용 출력

    if not token:
        print("❌ PUSHBULLET_API_KEY가 설정되지 않았습니다.")
        return False

    url = "https://api.pushbullet.com/v2/pushes"
    headers = {
        "Access-Token": token,
        "Content-Type": "application/json"
    }
    data = {
        "type": "note",
        "title": title,
        "body": body
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            print("✅ Pushbullet 전송 성공")
            return True
        else:
            print(f"❌ Pushbullet 전송 실패: {response.status_code} {response.text}")
            return False
    except Exception as e:
        print(f"❌ Pushbullet 예외 발생: {e}")
        return False
