import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText
import os

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.example.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "your_email@example.com")
SMTP_PASS = os.getenv("SMTP_PASS", "your_password")
SMTP_TO   = os.getenv("SMTP_TO", "recipient@example.com")

def send_pdf_report(pdf_path):
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = SMTP_TO
    msg['Subject'] = "[GIWANOS] 시스템 자동 점검 보고서"

    body = "첨부된 PDF 파일은 오늘 실행된 시스템 상태 점검 결과입니다.\n\n감사합니다."
    msg.attach(MIMEText(body, 'plain'))

    with open(pdf_path, "rb") as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(pdf_path)}')
        msg.attach(part)

    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USER, SMTP_PASS)
    server.send_message(msg)
    server.quit()
