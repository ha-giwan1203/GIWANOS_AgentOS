
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

# 환경변수 로드
load_dotenv("C:/giwanos/config/.env")

SMTP_SERVER = os.getenv("EMAIL_HOST")
SMTP_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASS")
EMAIL_RECEIVER = os.getenv("EMAIL_TO")

def send_test_email():
    try:
        logging.info(f"SMTP 서버 연결 시도 중: {SMTP_SERVER}:{SMTP_PORT}")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        logging.info("SMTP 서버 연결 성공!")

        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = EMAIL_RECEIVER
        msg['Subject'] = "GIWANOS 시스템 이메일 테스트"
        body = "이 이메일은 GIWANOS 시스템의 이메일 알림 테스트입니다."
        msg.attach(MIMEText(body, 'plain'))

        server.sendmail(EMAIL_USER, EMAIL_RECEIVER, msg.as_string())
        logging.info("✅ 이메일이 성공적으로 전송되었습니다.")
        server.quit()

    except Exception as e:
        logging.error(f"❌ 이메일 전송 실패: {e}")

if __name__ == "__main__":
    send_test_email()
