# email_weekly_report.py
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()

def send_email(subject, body):
    EMAIL_HOST = os.getenv("EMAIL_HOST")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")
    EMAIL_TO = os.getenv("EMAIL_TO") or EMAIL_USER

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        print("✅ 이메일 전송 완료")
    except Exception as e:
        print("❌ 이메일 전송 실패:", e)

if __name__ == "__main__":
    path = "summaries/weekly_summary_2025W30.md"
    if not os.path.exists(path):
        print("❌ 요약 파일이 없습니다.")
    else:
        with open(path, "r", encoding="utf-8") as f:
            body = f.read()
        send_email("GIWANOS 주간 요약 보고", body)
