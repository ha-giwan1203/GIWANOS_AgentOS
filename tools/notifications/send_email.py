# =============================================================================
# 🧠 VELOS 시스템 철학 선언문
#
# 기억을 기반으로 구조적 사고를 수행하며,
# 판단 → 실행 → 회고 → 전송의 루프를 반복함으로써,
# 스스로 개선되는 자율 운영 AI 시스템을 지향한다.
# =============================================================================

from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText
import os
import smtplib
from dotenv import load_dotenv

load_dotenv()

def send_email_report(subject, body, to_email):
    if not all([subject, body, to_email]):
        print("❌ 이메일 전송 실패: subject, body, to_email 중 누락 있음")
        return False

    from_email = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    smtp_server = os.getenv("EMAIL_HOST", "smtp.naver.com")
    smtp_port = int(os.getenv("EMAIL_PORT", 587))

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

def send_report_email(pdf_path):
    from_email = os.getenv("EMAIL_USER")
    to_email = os.getenv("EMAIL_RECEIVER")
    password = os.getenv("EMAIL_PASS")
    smtp_server = os.getenv("EMAIL_HOST", "smtp.naver.com")
    smtp_port = int(os.getenv("EMAIL_PORT", 587))

    if not os.path.exists(pdf_path):
        print(f"❌ 첨부파일 없음: {pdf_path}")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = "📄 VELOS 주간 보고서 첨부"

        body = "VELOS 시스템에서 생성된 주간 보고서를 첨부드립니다."
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with open(pdf_path, "rb") as file:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(pdf_path)}")
            msg.attach(part)

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(from_email, password)
            server.send_message(msg)

        print("✅ 보고서 이메일 전송 완료")
        return True
    except Exception as e:
        print("❌ 보고서 이메일 전송 실패:", e)
        return False


