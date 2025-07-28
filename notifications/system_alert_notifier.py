
import psutil
import smtplib
from email.mime.text import MIMEText
import logging
from dotenv import load_dotenv
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

load_dotenv('C:/giwanos/config/.env')  # 환경변수 파일 로드

SMTP_SERVER = os.getenv('EMAIL_HOST')
SMTP_PORT = int(os.getenv('EMAIL_PORT'))
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASS')
EMAIL_TO = os.getenv('EMAIL_TO')

CPU_THRESHOLD = 80.0
MEMORY_THRESHOLD = 80.0
DISK_THRESHOLD = 80.0

def check_system_conditions():
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent

    conditions = {
        'cpu': cpu,
        'memory': memory,
        'disk': disk
    }
    return conditions

def send_email_alert(subject, message):
    try:
        msg = MIMEText(message, 'plain', 'utf-8')
        msg['From'] = EMAIL_USER
        msg['To'] = EMAIL_TO
        msg['Subject'] = subject

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, EMAIL_TO, msg.as_string())

        logging.info('Alert email sent successfully.')
    except Exception as e:
        logging.error(f'Failed to send alert email: {e}')

def main():
    conditions = check_system_conditions()
    alerts = []

    if conditions['cpu'] > CPU_THRESHOLD:
        alerts.append(f"CPU usage high: {conditions['cpu']}%")

    if conditions['memory'] > MEMORY_THRESHOLD:
        alerts.append(f"Memory usage high: {conditions['memory']}%")

    if conditions['disk'] > DISK_THRESHOLD:
        alerts.append(f"Disk usage high: {conditions['disk']}%")

    if alerts:
        subject = f"🚨 System Alert - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        message = "\n".join(alerts)
        send_email_alert(subject, message)
    else:
        logging.info('System conditions within acceptable thresholds.')

if __name__ == "__main__":
    main()
