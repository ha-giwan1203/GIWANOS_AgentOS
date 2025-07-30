# C:/giwanos/evaluation/human_readable_reports/generate_pdf_report.py

import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generate_pdf_report(output_path: str = None):
    """
    GIWANOS 주간 보고서 PDF를 생성합니다.
    - output_path: 저장 경로 (지정하지 않으면 C:/giwanos/data/reports/weekly_report_YYYYMMDD.pdf)
    """
    # 저장 디렉토리 설정
    output_dir = os.path.join("C:", "giwanos", "data", "reports")
    os.makedirs(output_dir, exist_ok=True)

    # 기본 파일명 설정
    if not output_path:
        date_str = datetime.now().strftime("%Y%m%d")
        output_path = os.path.join(output_dir, f"weekly_report_{date_str}.pdf")

    # PDF 작성
    c = canvas.Canvas(output_path, pagesize=letter)
    c.drawString(100, 750, "GIWANOS Weekly Report")
    c.drawString(100, 730, f"Generated on: {datetime.now().isoformat()}")
    c.showPage()
    c.save()

    print(f"[generate_pdf_report] PDF created: {output_path}")
    return output_path
