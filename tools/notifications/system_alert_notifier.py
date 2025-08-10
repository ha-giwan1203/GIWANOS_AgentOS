# system_alert_notifier.py - 시스템 경고 알림을 Slack으로 전송

import os
from slack_api import send_slack_message

def notify_critical_alert(message):
    """
    시스템 경고 메시지를 지정된 Slack 채널로 전송합니다.
    """
    slack_channel = os.getenv("SLACK_ALERT_CHANNEL", "#alerts")
    try:
        result = send_slack_message(slack_channel, f"🚨 시스템 경고: {message}")
        if result.get("ok"):
            print("✅ 시스템 알림 전송 완료")
        else:
            print("❌ Slack 전송 실패:", result)
    except Exception as e:
        print("❌ 알림 전송 중 오류 발생:", str(e))


