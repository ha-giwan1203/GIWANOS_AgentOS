
from fpdf import FPDF
import os

# 경로 설정
report_path = "C:/giwanos/data/reports/velos_ai_insights_report.pdf"
font_path = "C:/giwanos/fonts/Nanum_Gothic/NanumGothic-Regular.ttf"

# 예시 데이터
report_data = {
    "summary": "이번 주 VELOS 시스템 상태는 양호합니다. 모든 에이전트가 정상 작동 중이며 장애는 발견되지 않았습니다.",
    "details": {
        "system_health.json": "CPU 및 메모리 사용량 정상",
        "api_cost_log.json": "API 호출 비용 예산 내 유지",
        "learning_memory.json": "메모리 업데이트 정상 작동"
    }
}

# 폰트 경로 확인
if not os.path.exists(font_path):
    print(f"❌ 폰트 파일이 존재하지 않습니다: {font_path}")
    exit(1)

pdf = FPDF()
pdf.add_page()

pdf.add_font("Nanum", "", font_path, uni=True)
pdf.set_font("Nanum", size=12)

pdf.cell(0, 10, "VELOS 시스템 주간 인사이트 보고서", ln=True)

pdf.ln(5)
summary_text = "요약:\n" + report_data["summary"]
pdf.multi_cell(0, 8, summary_text)

pdf.ln(5)
pdf.cell(0, 10, "주요 파일 상태:", ln=True)
for file, summary in report_data["details"].items():
    pdf.multi_cell(0, 8, f"{file}: {summary}")

pdf.output(report_path)
print("✅ PDF 리포트 생성 완료")


