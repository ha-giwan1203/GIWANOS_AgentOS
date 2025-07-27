
import os
import logging
from fpdf import FPDF
from datetime import datetime
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

logging.basicConfig(level=logging.INFO)
logging.getLogger('fontTools.subset').setLevel(logging.ERROR)

load_dotenv("C:/giwanos/config/.env")

MEMORY_PATH = "C:/giwanos/memory/learning_memory.json"
REPORTS_PATH = "C:/giwanos/data/reports"
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))

def create_pdf_report():
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('NanumGothic', '', 'C:/giwanos/Nanum_Gothic/NanumGothic-Regular.ttf')
    pdf.set_font("NanumGothic", size=14)
    pdf.cell(200, 10, text="GIWANOS 주간 보고서", align='C')
    pdf.ln(10)
    pdf.cell(200, 10, text=f"보고서 생성일: {datetime.now().strftime('%Y-%m-%d')}", align='C')
    pdf.ln(15)

    with open(MEMORY_PATH, 'r', encoding='utf-8') as file:
        import json
        memory_data = json.load(file)
        insights = memory_data.get("insights", [])[-5:]

    pdf.cell(200, 10, text="최근 인사이트:")
    pdf.ln(10)

    for idx, insight in enumerate(insights, 1):
        pdf.multi_cell(0, 10, text=f"{idx}. {insight['insight']} ({insight['timestamp']})")

    os.makedirs(REPORTS_PATH, exist_ok=True)
    report_filename = f"{REPORTS_PATH}/weekly_report_{datetime.now().strftime('%Y%m%d')}.pdf"
    pdf.output(report_filename)
    logging.info(f"[성공] PDF 보고서 생성 완료: {report_filename}")
    return report_filename

def send_report_via_email(report_file):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = EMAIL_TO
        msg['Subject'] = "GIWANOS 자동 생성 주간 보고서"

        with open(report_file, 'rb') as file:
            part = MIMEApplication(file.read(), Name=os.path.basename(report_file))
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(report_file)}"'
        msg.attach(part)

        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, EMAIL_TO, msg.as_string())
        server.quit()
        logging.info("[성공] PDF 보고서 이메일 전송 완료")
    except Exception as e:
        logging.error(f"[실패] PDF 보고서 이메일 전송 실패: {e}")

def generate_and_send_report():
    report_file = create_pdf_report()
    send_report_via_email(report_file)

if __name__ == "__main__":
    generate_and_send_report()
