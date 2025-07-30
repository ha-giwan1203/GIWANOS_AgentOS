
from evaluation.human_readable_reports.generate_pdf_report import create_pdf_from_insights

def run_system_insight_loop():
    insights = {"status": "모든 시스템이 정상적으로 작동합니다."}
    create_pdf_from_insights(insights)

if __name__ == "__main__":
    run_system_insight_loop()
