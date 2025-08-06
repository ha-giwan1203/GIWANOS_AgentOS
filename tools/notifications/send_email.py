
# C:/giwanos/tools/notifications/send_email.py

import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

def send_email_report(subject, body, to_email):
    from_email = os.getenv("SMTP_EMAIL")
    password = os.getenv("SMTP_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.naver.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(from_email, password)
            server.send_message(msg)
        print("✅ 이메일 전송 성공")
        return True
    except Exception as e:
        print("❌ 이메일 전송 실패:", e)
        return False
