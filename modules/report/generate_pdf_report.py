
from .report_data_loader import load_system_status, load_latest_reflection
from .report_formatter import export_to_markdown, export_to_html
from .summary_writer import write_summary_text
from fpdf import FPDF
from datetime import datetime
import os

class DynamicPDFReport(FPDF):
    def __init__(self, title="VELOS 시스템 인사이트 리포트"):
        super().__init__()
        self.title = title
        self.set_auto_page_break(auto=True, margin=15)
        self.font_path = "C:/giwanos/fonts/NotoSansKR-Regular.ttf"
        self.font_loaded = False
        if not os.path.exists(self.font_path):
            raise FileNotFoundError(f"❌ 폰트 파일이 존재하지 않습니다: {self.font_path}")
        try:
            self.add_font("NotoSans", "", self.font_path, uni=True)
            self.add_font("NotoSans", "B", self.font_path, uni=True)
            self.font_loaded = True
        except Exception as e:
            raise RuntimeError(f"❌ 폰트 로딩 실패: {e}")

    def header(self):
        if self.font_loaded:
            self.set_font("NotoSans", "B", 14)
        else:
            self.set_font("Arial", "B", 14)
        self.cell(0, 10, self.title, ln=True, align="C")
        self.ln(10)

    def section(self, title, content):
        if self.font_loaded:
            self.set_font("NotoSans", "B", 12)
            self.cell(0, 10, title, ln=True)
            self.set_font("NotoSans", "", 11)
        else:
            self.set_font("Arial", "B", 12)
            self.cell(0, 10, title, ln=True)
            self.set_font("Arial", "", 11)
        self.multi_cell(0, 8, content)
        self.ln()

def generate_pdf_report():
    system_status = load_system_status()
    reflection = load_latest_reflection()

    pdf = DynamicPDFReport()
    pdf.add_page()
    pdf.section("시스템 상태 로그", system_status)
    pdf.section("최신 리플렉션 요약", reflection)

    date_str = datetime.now().strftime("%Y-%m-%d")
    report_dir = "C:/giwanos/data/reports"
    os.makedirs(report_dir, exist_ok=True)

    if not os.access(report_dir, os.W_OK):
        raise PermissionError(f"❌ 보고서 디렉토리에 쓰기 권한이 없습니다: {report_dir}")

    pdf_path = f"{report_dir}/velos_ai_insights_report_{date_str}.pdf"
    try:
        pdf.output(pdf_path)
    except Exception as e:
        raise RuntimeError(f"❌ PDF 저장 중 오류 발생: {e}")

    export_to_markdown(system_status, reflection, report_dir, date_str)
    export_to_html(system_status, reflection, report_dir, date_str)
    write_summary_text(system_status, reflection, report_dir, date_str)

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"❌ PDF 파일이 생성되지 않았습니다: {pdf_path}")
    return pdf_path
