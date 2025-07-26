
import logging
from core.controller import Controller
from evaluation.human_readable_reports.generate_pdf_report import generate_and_send_report
import os

# 전체 로그 최소화 및 fontTools 로그 억제
logging.basicConfig(level=logging.ERROR, filename="C:/giwanos/data/logs/master_loop_execution.log", format='%(asctime)s %(levelname)s %(message)s')
logging.getLogger('fontTools.subset').setLevel(logging.ERROR)

PDF_REPORT_PATH = "C:/giwanos/data/reports/weekly_report_{}.pdf"
INSIGHT_REPORT_JSON = "C:/giwanos/data/reports/ai_insights.json"
INSIGHT_REPORT_PDF = "C:/giwanos/data/reports/ai_insights_report.pdf"
INSIGHT_REPORT_MD = "C:/giwanos/data/reports/ai_insights_report.md"
REFLECTION_MD_DIR = "C:/giwanos/data/reflection_md"

def main():
    try:
        controller = Controller()
        controller.run()

        generate_and_send_report()
        
        latest_weekly_pdf = PDF_REPORT_PATH.format(__import__('datetime').datetime.now().strftime('%Y%m%d'))
        
        print("[GIWANOS 시스템 실행 완료] 모든 작업이 성공적으로 처리되었습니다.")
        print("\n생성된 주요 보고서 및 문서 위치:")
        print(f"- 주간 보고서 (PDF): {latest_weekly_pdf}")
        print(f"- AI 인사이트 보고서 (JSON): {INSIGHT_REPORT_JSON}")
        print(f"- AI 인사이트 보고서 (Markdown): {INSIGHT_REPORT_MD}")
        print(f"- AI 인사이트 보고서 (PDF): {INSIGHT_REPORT_PDF}")
        print(f"- 회고 파일 위치 (최신): {REFLECTION_MD_DIR}")

    except Exception as e:
        print("[GIWANOS 시스템 오류] 다음 작업에서 오류가 발생했습니다:")
        print(f"- 오류 내용: {e}")
        logging.error(f"실행 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
