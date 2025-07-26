
import requests
import logging
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
load_dotenv("C:/giwanos/config/.env")

MOBILE_NOTIFICATION_URL = os.getenv("MOBILE_NOTIFICATION_URL")
NOTIFICATION_TOKEN = os.getenv("NOTIFICATION_TOKEN")

def send_mobile_notification(message):
    headers = {
        "Access-Token": NOTIFICATION_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "type": "note",
        "title": "GIWANOS 알림",
        "body": message
    }

    response = requests.post(MOBILE_NOTIFICATION_URL, json=payload, headers=headers)

    logging.info(f"API 응답 상태코드: {response.status_code}")
    logging.info(f"API 응답 내용: {response.text}")

    if response.status_code == 200:
        logging.info("[성공] 모바일 알림이 정상적으로 전송되었습니다.")
    else:
        logging.error(f"[실패] 모바일 알림 전송 실패: {response.status_code}, {response.text}")

if __name__ == "__main__":
    send_mobile_notification("GIWANOS 시스템 모바일 알림 테스트 메시지입니다.")
