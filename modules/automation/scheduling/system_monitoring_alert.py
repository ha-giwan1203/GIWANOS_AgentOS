# modules/automation/scheduling/system_monitoring_alert.py
import psutil
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv('C:/giwanos/.env')

CPU_THRESHOLD = 90
MEMORY_THRESHOLD = 90
DISK_THRESHOLD = 90

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def send_alert(message):
    data = {"text": message}
    requests.post(SLACK_WEBHOOK_URL, json=data)


# 시스템 리소스 상태 검사
def check_system_status():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent

    alert_message = []

    if cpu_usage > CPU_THRESHOLD:
        alert_message.append(f"🚨 높은 CPU 사용량: {cpu_usage}%")
    if memory_usage > MEMORY_THRESHOLD:
        alert_message.append(f"🚨 높은 메모리 사용량: {memory_usage}%")
    if disk_usage > DISK_THRESHOLD:
        alert_message.append(f"🚨 높은 디스크 사용량: {disk_usage}%")

    if alert_message:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        full_message = f"[{timestamp}] 시스템 리소스 경고:\n" + "\n".join(alert_message)
        send_alert(full_message)
        print(full_message)
    else:
        print("모든 시스템 리소스 정상 범위 내.")


if __name__ == '__main__':
    check_system_status()
