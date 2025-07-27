# C:/giwanos/run_giwanos_master_loop.py

import os
import logging
import shutil

from core.auto_optimization_cleanup import main as cleanup_main
from notion_integration.notion_sync import main as notion_sync
from automation.git_management.git_sync import main as git_sync
from evaluation.giwanos_agent.judge_agent import JudgeAgent
from evaluation.human_readable_reports.generate_pdf_report import generate_pdf_report
from notifications.send_email import send_test_email as send_report_email
from interface.status_dashboard import main as update_dashboard

# --- Logging Configuration ---
log_dir = os.path.abspath(os.path.join("C:", os.sep, "giwanos", "data", "logs"))
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "master_loop_execution.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode="a", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    logger.info("=== GIWANOS Master Loop Start ===")

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

    logger.info("=== GIWANOS Master Loop End ===")
    logger.info("")  # blank line

if __name__ == "__main__":
    main()
