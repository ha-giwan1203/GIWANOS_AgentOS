# C:/giwanos/run_giwanos_master_loop.py

import os
import logging
import shutil
import warnings
import psutil

warnings.filterwarnings('ignore', 'Thread.*missing ScriptRunContext.*',
                        module='streamlit.runtime.scriptrunner_utils')

# Logging setup
LOG_DIR = os.path.join("C:", os.sep, "giwanos", "data", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "master_loop_execution.log")

logging.basicConfig(
    filename=LOG_FILE,
    filemode='a',
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    force=True
)
logger = logging.getLogger()

# Core functions
from core.auto_optimization_cleanup import main as cleanup_main
from notion_integration.notion_sync import main as notion_sync
from automation.git_management.git_sync import main as git_sync
from evaluation.giwanos_agent.judge_agent import JudgeAgent
from evaluation.human_readable_reports.generate_pdf_report import generate_pdf_report
from notifications.send_email import send_test_email as send_report_email

def main():
    logger.info("=== GIWANOS Master Loop Start ===")

    cleanup_main()
    notion_sync()
    shutil.rmtree(os.path.join("C:", "giwanos", ".tmp.driveupload"), ignore_errors=True)
    git_sync()

    # JudgeAgent with its own log handler
    agent_logger = logging.getLogger("judge_agent")
    for h in list(agent_logger.handlers):
        agent_logger.removeHandler(h)
    agent_log_file = os.path.join(LOG_DIR, "judge_agent.log")
    handler = logging.FileHandler(agent_log_file, mode='a', encoding='utf-8')
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    agent_logger.addHandler(handler)

    agent = JudgeAgent()
    agent.run()
    for h in agent_logger.handlers:
        h.flush()

    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("C:/giwanos").percent
    logger.info(f"[perf] cpu={cpu:.1f}, mem={mem:.1f}, disk={disk:.1f}")

    generate_pdf_report()
    send_report_email()

    # Snapshot creation with safe imports
    try:
        from core.hybrid_snapshot_manager import HybridSnapshotManager
        HybridSnapshotManager().create_incremental_snapshot()
    except Exception as e:
        logger.warning(f"Skipping incremental snapshot: {e}")

    try:
        from core.snapshot_manager import SnapshotManager
        SnapshotManager().create_full_snapshot()
    except Exception as e:
        logger.warning(f"Skipping full snapshot: {e}")

    # Weekly summary stub
    from datetime import date
    today = date.today()
    year, week, _ = today.isocalendar()
    summary_path = f"C:/giwanos/data/reports/weekly_summary_{year}W{week}.md"
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"# Weekly Summary {year}W{week}\nGenerated on {today.isoformat()}\n")
    logger.info(f"Weekly summary created: {summary_path}")

    logger.info("=== GIWANOS Master Loop End ===")

if __name__ == "__main__":
    main()
