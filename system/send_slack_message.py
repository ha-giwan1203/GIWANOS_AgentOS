import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)


import os
import requests

slack_token = os.getenv("SLACK_BOT_TOKEN")
channel_id = os.getenv("SLACK_CHANNEL_ID")

headers = {
    "Authorization": f"Bearer {slack_token}",
    "Content-Type": "application/json"
}

data = {
    "channel": channel_id,
    "text": "✅ GIWAN 지니봇 테스트 메시지입니다!",
    "username": "giwan-bot",
    "icon_emoji": ":robot_face:"
}

response = requests.post("https://slack.com/api/chat.postMessage", headers=headers, json=data)
print(response.json())
