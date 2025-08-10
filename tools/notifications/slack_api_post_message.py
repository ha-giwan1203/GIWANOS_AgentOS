# slack_api_post_message.py - 슬랙 메시지를 전송하는 단독 실행 스크립트

import sys
from slack_api import send_slack_message

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("사용법: python slack_api_post_message.py [채널명] [메시지]")
        sys.exit(1)

    channel = sys.argv[1]
    message = " ".join(sys.argv[2:])
    result = send_slack_message(channel, message)
    
    if result.get("ok"):
        print("✅ Slack 메시지 전송 성공")
    else:
        print("❌ 전송 실패:", result)


