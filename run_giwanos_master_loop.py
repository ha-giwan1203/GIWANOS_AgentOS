import os
import sys
import logging
import warnings
from datetime import datetime
from pathlib import Path

# suppress unwanted streamlit warnings
warnings.filterwarnings(
    'ignore', 'Thread.*missing ScriptRunContext.*',
    module='streamlit.runtime.scriptrunner_utils'
)

# -------------------------------------------------------------------
# Constants & Paths
# -------------------------------------------------------------------
ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / 'data'
SNAPSHOT_DIR = DATA_DIR / 'snapshots'
REPORT_DIR = DATA_DIR / 'reports'
LOG_DIR = DATA_DIR / 'logs'

# -------------------------------------------------------------------
# Directory Creation
# -------------------------------------------------------------------
for directory in (SNAPSHOT_DIR, REPORT_DIR, LOG_DIR):
    directory.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------------
# Logger Setup
# -------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler(LOG_DIR / 'master_loop_execution.log')
handler.setFormatter(
    logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
)
logger.addHandler(handler)

# -------------------------------------------------------------------
# Imports of Project Modules
# -------------------------------------------------------------------
try:
    from evaluation.giwanos_agent.judge_agent import JudgeAgent
    from core.snapshot_manager import create_incremental_snapshot, create_full_snapshot
    from evaluation.human_readable_reports.generate_pdf_report import generate_pdf_report
    from notifications.send_email import send_report_email
    from notion_integration.notion_sync import main as notion_sync
    from automation.git_management.git_sync import main as git_sync
except ImportError as err:
    logger.exception('Module import failed: %s', err)
    sys.exit(1)

# -------------------------------------------------------------------
# Step Functions
# -------------------------------------------------------------------

def snapshot_step():
    today = datetime.now().strftime('%Y%m%d')
    inc_dir = SNAPSHOT_DIR / f'incremental_snapshot_{today}'
    try:
        create_incremental_snapshot(inc_dir)
        logger.info('Incremental snapshot created: %s', inc_dir)
    except Exception as e:
        logger.warning('Incremental snapshot skipped: %s', e)
        full_dir = SNAPSHOT_DIR / f'full_snapshot_{today}'
        try:
            create_full_snapshot(full_dir)
            logger.info('Full snapshot created: %s', full_dir)
        except Exception as ex:
            logger.warning('Full snapshot skipped: %s', ex)


def run_judge_agent():
    try:
        agent = JudgeAgent()
        agent.run()
        logger.info('JudgeAgent completed')
    except Exception as e:
        logger.exception('JudgeAgent failed: %s', e)


def sync_notion_step():
    try:
        notion_sync()
        logger.info('Notion sync completed')
    except Exception as e:
        logger.exception('Notion sync failed: %s', e)


def sync_git_step():
    try:
        git_sync()
        logger.info('Git sync completed')
    except Exception as e:
        logger.exception('Git sync failed: %s', e)


def report_and_email_step():
    try:
        pdf_path = generate_pdf_report()
        logger.info('PDF report generated: %s', pdf_path)
    except Exception as e:
        logger.exception('Report generation failed: %s', e)
        return
    try:
        send_report_email(pdf_path)
        logger.info('Report email sent')
    except Exception as e:
        logger.exception('Email sending failed: %s', e)


def weekly_summary_step():
    try:
        from evaluation.summary.weekly_summary import generate_weekly_summary
        summary_path = generate_weekly_summary(REPORT_DIR)
        logger.info('Weekly summary created: %s', summary_path)
    except ImportError:
        logger.warning('Weekly summary module missing')
    except Exception as e:
        logger.exception('Weekly summary failed: %s', e)

# -------------------------------------------------------------------
# Main Entry Point
# -------------------------------------------------------------------

def main():
    logger.info('=== GIWANOS Master Loop Start ===')
    snapshot_step()
    run_judge_agent()
    sync_notion_step()
    sync_git_step()
    report_and_email_step()
    weekly_summary_step()
    logger.info('=== GIWANOS Master Loop End ===')


if __name__ == '__main__':
    main()
