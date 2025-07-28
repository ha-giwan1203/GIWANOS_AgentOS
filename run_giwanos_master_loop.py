import logging
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler('C:/giwanos/data/logs/master_loop_execution.log'),
        logging.StreamHandler(sys.stdout)
    ],
    format='%(asctime)s [%(levelname)s] %(message)s'
)

logger = logging.getLogger(__name__)

# 실제 사용되는 모듈 import (최종적으로 명시)
from core.snapshot_manager import create_incremental_snapshot, create_full_snapshot
from evaluation.giwanos_agent.judge_agent import JudgeAgent
from notion_integration.notion_sync import main as notion_sync
from automation.git_management.git_sync import main as git_sync
from evaluation.human_readable_reports.generate_pdf_report import generate_pdf_report
from notifications.send_email import send_report_email
from scheduling.weekly_summary import generate_weekly_summary
from advanced_modules.cot_evaluator import evaluate_cot
from advanced_modules.advanced_rag import test_advanced_rag
from core.auto_recovery_agent import main as auto_recovery_main
from core.reflection_agent import run_reflection
from core.adaptive_reasoning_agent import adaptive_reasoning_main
from core.threshold_optimizer import threshold_optimizer_main
from core.rule_optimizer import rule_optimizer_main
from core.system_health_logger import update_system_health

def snapshot_step():
    try:
        create_incremental_snapshot()
        logger.info('Incremental snapshot created')
    except Exception as e:
        logger.warning(f'Incremental snapshot skipped: {e}')
        try:
            create_full_snapshot()
            logger.info('Full snapshot created')
        except Exception as ex:
            logger.warning(f'Full snapshot skipped: {ex}')

def run_judge_agent():
    try:
        agent = JudgeAgent()
        agent.run()
        logger.info('JudgeAgent completed')
    except Exception as e:
        logger.exception(f'JudgeAgent failed: {e}')

def report_and_email_step():
    try:
        pdf_path = generate_pdf_report()
        logger.info(f'PDF report generated: {pdf_path}')
    except Exception as e:
        logger.exception(f'Report generation failed: {e}')
        return
    try:
        send_report_email(pdf_path)
        logger.info('Report email sent')
    except Exception as e:
        logger.exception(f'Email sending failed: {e}')

def weekly_summary_step():
    try:
        report_dir = "C:/giwanos/data/reports"
        summary_path = generate_weekly_summary(report_dir)
        logger.info(f'Weekly summary created: {summary_path}')
    except Exception as e:
        logger.exception(f'Weekly summary failed: {e}')

def main():
    logger.info('=== GIWANOS Master Loop Start ===')
    update_system_health()

    snapshot_step()
    run_judge_agent()
    notion_sync()
    git_sync()
    report_and_email_step()
    weekly_summary_step()
    evaluate_cot()
    test_advanced_rag()
    auto_recovery_main()
    run_reflection()

    # Adaptive Reasoning 관련 새롭게 추가된 루틴 실행
    adaptive_reasoning_main()
    threshold_optimizer_main()
    rule_optimizer_main()

    logger.info('=== GIWANOS Master Loop End ===')

if __name__ == '__main__':
    main()
