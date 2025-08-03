import os
import requests
from dotenv import load_dotenv

# .env 파일 정확한 경로에서 로드
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env"))

token = os.getenv("SLACK_BOT_TOKEN")
channel = os.getenv("SLACK_CHANNEL_ID")

print("[DEBUG] 불러온 채널 ID:", channel)
print("[DEBUG] 불러온 토큰 일부:", token[:15] + "..." if token else "None")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

payload = {
    "channel": channel,
    "text": "✅ VELOS 시스템: Slack API 메서드(chat.postMessage) 전송 성공 테스트"
}

response = requests.post("https://slack.com/api/chat.postMessage", headers=headers, json=payload)

print("[DEBUG] Slack 응답 상태 코드:", response.status_code)
print("[DEBUG] Slack 응답 내용:", response.json())
