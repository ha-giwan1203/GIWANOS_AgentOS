import os
from fpdf import FPDF
import logging
from datetime import datetime

BASE_DIR = "C:/giwanos"
pdf_dir = os.path.join(BASE_DIR, "data/reports")
os.makedirs(pdf_dir, exist_ok=True)

logger = logging.getLogger("pdf_test")
logger.setLevel(logging.INFO)

if not logger.handlers:
    logger.addHandler(logging.FileHandler('C:/giwanos/data/logs/pdf_test.log'))
    logger.addHandler(logging.StreamHandler())

def test_pdf_generation():
    try:
        pdf = FPDF()
        pdf.add_page()

        # 수정된 정확한 폰트 경로
        font_path = "C:/giwanos/fonts/NanumGothic-Regular.ttf"
        if not os.path.exists(font_path):
            logger.error(f"폰트 파일이 존재하지 않음: {font_path}")
            return

        pdf.add_font("NanumGothic", "", font_path, uni=True)
        pdf.set_font("NanumGothic", size=12)
        
        pdf.cell(200, 10, txt="VELOS 주간 보고서", ln=True, align='C')
        report_content = f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        pdf.cell(200, 10, txt=report_content, ln=True)

        pdf_path = os.path.join(pdf_dir, "weekly_report_test.pdf")
        pdf.output(pdf_path)

        logger.info(f"✅ PDF 테스트 보고서가 생성됨: {pdf_path}")

    except Exception as e:
        logger.error(f"❌ PDF 테스트 보고서 생성 실패: {e}")

if __name__ == '__main__':
    test_pdf_generation()


