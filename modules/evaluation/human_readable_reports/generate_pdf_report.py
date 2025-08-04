
from fpdf import FPDF
import datetime
import os
import warnings

# ⚠️ 콘솔에 경고 출력되지 않도록 설정
warnings.filterwarnings("ignore", category=UserWarning)

report_content = {'system_summary': {'cpu_usage': '25%', 'memory_usage': '45%', 'disk_usage': '60%', 'recent_events': ['JudgeAgent 정상 실행', 'GitHub 자동 커밋 완료']}, 'analysis_details': {'advanced_rag_test': 'API 호출 효율성: 80% 감소 (총 호출 20회)', 'cot_evaluation': '점수: 95.2점, 순위: 1위', 'threshold_rule_optimization': 'Threshold 및 Rule 최적화 완료'}, 'recent_git_commits': ['자동 커밋: 최신 파일 자동 백업', 'data_load_test.py 추가', 'generate_pdf_report.py 제거'], 'issues_summary': '이번 주 특별한 장애나 예외 사항 없음.'}

font_path = r"C:\giwanos\fonts\NotoSansKR-Regular.ttf"

class ImprovedPDFReport(FPDF):
    def header(self):
        self.set_font('NotoSansKR', 'B', 14)
        self.cell(0, 10, 'VELOS 상세 주간 보고서', ln=True, align='C')

    def footer(self):
        self.set_y(-15)
        self.set_font('NotoSansKR', '', 8)
        self.cell(0, 10, f'페이지 {self.page_no()}', 0, 0, 'C')

    def add_report_section(self, title, content):
        self.set_font('NotoSansKR', 'B', 12)
        self.cell(0, 10, title, ln=True)
        self.set_font('NotoSansKR', '', 11)
        if isinstance(content, dict):
            for key, value in content.items():
                if isinstance(value, list):
                    self.cell(0, 8, f"{key.replace('_', ' ').capitalize()}:", ln=True)
                    for item in value:
                        self.cell(10)
                        self.cell(0, 8, f"- {item}", ln=True)
                else:
                    self.cell(0, 8, f"{key.replace('_', ' ').capitalize()}: {value}", ln=True)
        elif isinstance(content, list):
            for item in content:
                self.cell(0, 8, f"- {item}", ln=True)
        else:
            self.multi_cell(0, 8, content)
        self.ln(5)

def create_weekly_report():
    now = datetime.datetime.now()
    pdf = ImprovedPDFReport()
    pdf.add_font('NotoSansKR', '', font_path, uni=True)
    pdf.add_font('NotoSansKR', 'B', font_path, uni=True)
    pdf.add_page()

    pdf.set_font('NotoSansKR', '', 10)
    pdf.cell(0, 10, f"생성 일시: {now.isoformat()}", ln=True)
    pdf.ln(5)

    pdf.add_report_section("1. 시스템 상태 요약", report_content["system_summary"])
    pdf.add_report_section("2. 분석 결과 상세 내역", report_content["analysis_details"])
    pdf.add_report_section("3. 최근 Git 커밋 내역", report_content["recent_git_commits"])
    pdf.add_report_section("4. 장애 및 예외 사항 요약", report_content["issues_summary"])

    output_dir = r"C:/giwanos/data/reports"
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f'weekly_report_{now.strftime("%Y%m%d")}.pdf')
    pdf.output(pdf_path)
    print(f"✅ 보고서 생성 완료: {pdf_path}")

# ▶ alias 추가 – 마스터 루프에서 호출 가능하도록
generate_pdf_report = create_weekly_report

if __name__ == "__main__":
    create_weekly_report()
