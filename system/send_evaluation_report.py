
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))

log_path = Path("logs/evaluation_aggregated_log.jsonl")
pdf_dir = Path("reports")
if not log_path.exists():
    print("❌ 통합 로그가 없습니다.")
    exit()
if not pdf_dir.exists():
    print("❌ PDF 폴더가 없습니다.")
    exit()

# 최신 PDF 파일 찾기
pdf_files = sorted(pdf_dir.glob("evaluation_report_*.pdf"), key=os.path.getmtime, reverse=True)
latest_pdf = pdf_files[0] if pdf_files else None
if not latest_pdf:
    print("❌ PDF 파일이 없습니다.")
    exit()

# 이메일 구성
msg = EmailMessage()
msg["Subject"] = "📊 GIWANOS 평가 보고서 자동 전송"
msg["From"] = EMAIL_USER
msg["To"] = EMAIL_TO

recent_lines = log_path.read_text(encoding="utf-8").splitlines()[-5:]
summary = "\n".join(recent_lines)

msg.set_content(f"""안녕하세요, 지완님.

다음은 최신 GIWANOS 평가 보고서 요약입니다:

{summary}

전체 보고서는 첨부된 PDF 파일을 확인해 주세요.
""")

# PDF 첨부
with open(latest_pdf, "rb") as f:
    msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=latest_pdf.name)

try:
    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
    print("✅ 이메일 전송 완료 + PDF 첨부됨 →", latest_pdf.name)
except Exception as e:
    print("❌ 이메일 전송 실패:", e)
