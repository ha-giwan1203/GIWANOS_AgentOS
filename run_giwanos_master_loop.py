# C:/giwanos/run_giwanos_master_loop.py

import os
import logging
import shutil
import warnings
import psutil

# Configure logging immediately
LOG_DIR = os.path.join("C:", os.sep, "giwanos", "data", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "master_loop_execution.log")

logging.basicConfig(
    filename=LOG_FILE,
    filemode='a',
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    force=True  # ensures reconfiguration
)
logger = logging.getLogger()

# Suppress specific Streamlit warnings
warnings.filterwarnings(
    'ignore',
    'Thread.*missing ScriptRunContext.*',
    module='streamlit.runtime.scriptrunner_utils'
)

from core.auto_optimization_cleanup import main as cleanup_main
from notion_integration.notion_sync import main as notion_sync
from automation.git_management.git_sync import main as git_sync
from evaluation.giwanos_agent.judge_agent import JudgeAgent
from evaluation.human_readable_reports.generate_pdf_report import generate_pdf_report
from notifications.send_email import send_test_email as send_report_email

def main():
    logger.info("=== GIWANOS Master Loop Start ===")

    # 1) Cleanup
    cleanup_main()
    # 2) Notion sync
    notion_sync()
    # 3) Temp cleanup
    shutil.rmtree("C:/giwanos/.tmp.driveupload", ignore_errors=True)
    # 4) Git sync
    git_sync()
    # 5) Agent run
    agent = JudgeAgent()
    agent.run()
    # 6) Performance log
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("C:/giwanos").percent
    logger.info(f"[perf] cpu={cpu:.1f}, mem={mem:.1f}, disk={disk:.1f}")
    # 7) PDF & email
    generate_pdf_report()
    send_report_email()

    logger.info("=== GIWANOS Master Loop End ===")

if __name__ == "__main__":
    main()
