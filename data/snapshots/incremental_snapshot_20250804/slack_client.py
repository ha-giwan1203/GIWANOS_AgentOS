import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

# 정확한 실제 .env 파일 위치
env_path = "C:/giwanos/configs/.env"
load_dotenv(env_path)

class SlackClient:
    def __init__(self):
        self.token = os.getenv("SLACK_BOT_TOKEN")
        self.default_channel = os.getenv("SLACK_DEFAULT_CH", "#general")
        self.client = WebClient(token=self.token)

        if not self.token:
            raise ValueError(f"환경변수 SLACK_BOT_TOKEN이 설정되지 않았습니다. 현재 .env 경로: {env_path}")

    def send_message(self, channel, message):
        try:
            response = self.client.chat_postMessage(channel=channel, text=message)
            return f"Slack 메시지 전송 성공: {response['ts']}"
        except SlackApiError as e:
            return f"Slack 메시지 전송 실패: {e.response['error']}"


