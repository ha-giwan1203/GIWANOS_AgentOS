
from modules.core.time_utils import now_utc, now_kst, iso_utc, monotonic
import json
import logging
import os
from fpdf import FPDF
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logging.getLogger('fontTools.subset').setLevel(logging.WARNING)

INSIGHT_REPORT_PATH = "C:/giwanos/data/reports/ai_insights.json"
MARKDOWN_REPORT_PATH = "C:/giwanos/data/reports/ai_insights_report.md"
PDF_REPORT_PATH = "C:/giwanos/data/reports/ai_insights_report.pdf"

def load_insights():
    try:
        with open(INSIGHT_REPORT_PATH, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"인사이트 데이터 로드 실패: {e}")
        return {"generated_at": "", "insights": []}

def save_markdown_report(insights_data):
    lines = ["# GIWANOS AI 인사이트 보고서", f"생성 일시: {insights_data['generated_at']}\n"]
    for insight in insights_data["insights"]:
        lines.append(f"### {insight['metric']}")
        lines.append(f"- 점수: {insight['score']}")
        lines.append(f"- 인사이트: {insight['insight']}\n")

    with open(MARKDOWN_REPORT_PATH, 'w', encoding='utf-8') as file:
        file.write("\n".join(lines))
    logging.info("Markdown 보고서 생성 완료")

def save_pdf_report(insights_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('NanumGothic', '', 'C:/giwanos/Nanum_Gothic/NanumGothic-Regular.ttf')
    pdf.set_font("NanumGothic", size=14)
    pdf.cell(200, 10, text="GIWANOS AI 인사이트 보고서", align='C')
    pdf.ln(10)
    pdf.cell(200, 10, text=f"생성 일시: {insights_data['generated_at']}", align='C')
    pdf.ln(15)

    for insight in insights_data["insights"]:
        pdf.cell(0, 10, text=f"{insight['metric']} ({insight['score']}점)")
        pdf.ln(8)
        pdf.multi_cell(0, 10, text=f"인사이트: {insight['insight']}")
        pdf.ln(5)

    pdf.output(PDF_REPORT_PATH)
    logging.info("PDF 보고서 생성 완료")

def main():
    insights_data = load_insights()
    save_markdown_report(insights_data)
    save_pdf_report(insights_data)

if __name__ == "__main__":
    main()



