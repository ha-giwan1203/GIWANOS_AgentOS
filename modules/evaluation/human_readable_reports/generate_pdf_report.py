
from fpdf import FPDF
import datetime
import os
import warnings
import json

warnings.filterwarnings("ignore", category=UserWarning)

font_path = r"C:\giwanos\fonts\NotoSansKR-Regular.ttf"
health_log = r"C:/giwanos/data/logs/system_health.json"
reflection_dir = r"C:/giwanos/data/reflections"
report_dir = r"C:/giwanos/data/reports"

def load_latest_reflection():
    if not os.path.exists(reflection_dir):
        return "리플렉션 데이터 없음"
    files = sorted([f for f in os.listdir(reflection_dir) if f.endswith(".json")])
    if not files:
        return "리플렉션 데이터 없음"
    with open(os.path.join(reflection_dir, files[-1]), "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return data.get("summary", "요약 없음")
        except:
            return "리플렉션 파싱 실패"

def load_system_status():
    if not os.path.exists(health_log):
        return "시스템 상태 로그 없음"
    with open(health_log, "r", encoding="utf-8") as f:
        try:
            return f.read()[-800:]  # 최근 로그 일부
        except:
            return "시스템 상태 파싱 실패"

def export_to_markdown(date_str, sections):
    md_path = os.path.join(report_dir, f"weekly_report_{date_str}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        for title, content in sections:
            f.write(f"## {title}\n\n{content}\n\n")
    return md_path

def export_to_html(date_str, sections):
    html_path = os.path.join(report_dir, f"weekly_report_{date_str}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write("<html><head><meta charset='utf-8'><title>VELOS 보고서</title></head><body>")
        for title, content in sections:
            f.write(f"<h2>{title}</h2><pre>{content}</pre>")
        f.write("</body></html>")
    return html_path

class DynamicPDFReport(FPDF):
    def header(self):
        self.set_font('NotoSansKR', 'B', 14)
        self.cell(0, 10, 'VELOS 동적 주간 보고서', ln=True, align='C')

    def footer(self):
        self.set_y(-15)
        self.set_font('NotoSansKR', '', 8)
        self.cell(0, 10, f'페이지 {self.page_no()}', 0, 0, 'C')

    def section(self, title, content):
        self.set_font('NotoSansKR', 'B', 12)
        self.cell(0, 10, title, ln=True)
        self.set_font('NotoSansKR', '', 11)
        self.multi_cell(0, 8, content)
        self.ln(5)

def generate_pdf_report():
    now = datetime.datetime.now()
    date_str = now.strftime("%Y%m%d")
    os.makedirs(report_dir, exist_ok=True)

    # Load data
    syslog = load_system_status()
    reflection = load_latest_reflection()

    sections = [
        ("1. 최근 시스템 상태 로그", syslog),
        ("2. 최신 리플렉션 요약", reflection),
        ("3. 기타 항목", "CoT, RAG, Threshold 평가 등은 자동 로그에 반영됨")
    ]

    # PDF 생성
    pdf = DynamicPDFReport()
    pdf.add_font('NotoSansKR', '', font_path, uni=True)
    pdf.add_font('NotoSansKR', 'B', font_path, uni=True)
    pdf.add_page()
    pdf.set_font('NotoSansKR', '', 10)
    pdf.cell(0, 10, f"생성 일시: {now.isoformat()}", ln=True)
    pdf.ln(5)
    for title, content in sections:
        pdf.section(title, content)

    pdf_path = os.path.join(report_dir, f'weekly_report_{date_str}.pdf')
    pdf.output(pdf_path)

    # Markdown & HTML 동시 생성
    md_path = export_to_markdown(date_str, sections)
    html_path = export_to_html(date_str, sections)

    # GPT 요약용 raw 텍스트 저장
    with open(os.path.join(report_dir, f"weekly_summary_{date_str}.txt"), "w", encoding="utf-8") as f:
        for title, content in sections:
            f.write(f"{title}\n{content}\n\n")

    print(f"✅ 보고서 생성 완료: {pdf_path}")
    return pdf_path

# 마스터 루프 호환
create_weekly_report = generate_pdf_report

if __name__ == "__main__":
    generate_pdf_report()
