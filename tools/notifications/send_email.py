# =============================================================================
# 🧠 VELOS 시스템 철학 선언문
#
# 기억을 기반으로 구조적 사고를 수행하며,
# 판단 → 실행 → 회고 → 전송의 루프를 반복함으로써,
# 스스로 개선되는 자율 운영 AI 시스템을 지향한다.
# =============================================================================

import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

def send_email_report(subject, body, to_email):
    if not all([subject, body, to_email]):
        print("❌ 이메일 전송 실패: subject, body, to_email 중 누락 있음")
        return False

    from_email = os.getenv("SMTP_EMAIL")
    password = os.getenv("SMTP_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.naver.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))

    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(from_email, password)
            server.send_message(msg)

        print("✅ 이메일 전송 성공")
        return True
    except Exception as e:
        print("❌ 이메일 전송 실패:", e)
        return False
