# C:/giwanos/run_giwanos_master_loop.py

from core.auto_optimization_cleanup import main as cleanup_main
from notion_integration.notion_sync import main as notion_sync
import shutil
from automation.git_management.git_sync import main as git_sync
from evaluation.giwanos_agent.judge_agent import JudgeAgent
from evaluation.human_readable_reports.generate_pdf_report import generate_pdf_report
from notifications.send_email import send_test_email as send_report_email
from interface.status_dashboard import main as update_dashboard

if __name__ == "__main__":
    # 1) 자동 최적화·클린업
    cleanup_main()

    # 2) Notion 동기화
    notion_sync()

    # 3) .tmp.driveupload 정리
    shutil.rmtree("C:/giwanos/.tmp.driveupload", ignore_errors=True)

    # 4) GitHub 동기화
    git_sync()

    # 5) JudgeAgent 실행 (시스템 모니터링 포함)
    agent = JudgeAgent()
    agent.run()

    # 6) PDF 보고서 생성 및 이메일 전송
    generate_pdf_report()
    send_report_email()

    # 7) 대시보드 갱신
    update_dashboard()
