
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
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

# test용 이메일 함수
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
        logging.info("✅ 테스트 이메일이 성공적으로 전송되었습니다.")
        server.quit()

    except Exception as e:
        logging.error(f"❌ 테스트 이메일 전송 실패: {e}")

# 보고서 이메일 함수
def send_report_email(pdf_path):
    try:
        logging.info(f"SMTP 서버 연결 시도 중: {SMTP_SERVER}:{SMTP_PORT}")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        logging.info("SMTP 서버 연결 성공!")

        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = EMAIL_RECEIVER
        msg['Subject'] = "GIWANOS 시스템 보고서"
        msg.attach(MIMEText("첨부된 파일은 GIWANOS 시스템에서 생성한 보고서입니다.", 'plain'))

        # PDF 첨부
        with open(pdf_path, 'rb') as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(pdf_path))
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(pdf_path)}"'
        msg.attach(part)

        server.sendmail(EMAIL_USER, EMAIL_RECEIVER, msg.as_string())
        logging.info("✅ 보고서 이메일이 성공적으로 전송되었습니다.")
        server.quit()

    except Exception as e:
        logging.error(f"❌ 보고서 이메일 전송 실패: {e}")
