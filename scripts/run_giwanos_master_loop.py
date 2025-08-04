
import logging
import sys
import os
from datetime import datetime

# 경로 설정
BASE_DIR = "C:/giwanos"

# PYTHONPATH 설정 (VELOS 기준 명확히 설정)
sys.path.append(BASE_DIR)

# 로그 설정
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler(f'{BASE_DIR}/data/logs/master_loop_execution.log'),
        logging.StreamHandler(sys.stdout)
    ],
    format='%(asctime)s [%(levelname)s] %(message)s'
)

logger = logging.getLogger(__name__)

# VELOS 최신 모듈 경로 기준 import
from modules.core.hybrid_snapshot_manager import create_incremental_snapshot, create_full_snapshot
from modules.core.auto_recovery_agent import main as auto_recovery_main
from modules.core.reflection_agent import run_reflection
from modules.evaluation.giwanos_agent.judge_agent import JudgeAgent
from modules.automation.git_management.git_sync import main as git_sync
from modules.evaluation.human_readable_reports.generate_pdf_report import generate_pdf_report
from tools.notifications.send_email import send_report_email
from modules.automation.scheduling.weekly_summary import generate_weekly_summary
from modules.advanced.advanced_modules.cot_evaluator import evaluate_cot
from modules.advanced.advanced_modules.advanced_rag import test_advanced_rag
from modules.core.adaptive_reasoning_agent import adaptive_reasoning_main
from modules.core.threshold_optimizer import threshold_optimizer_main
from modules.core.rule_optimizer import rule_optimizer_main
from modules.automation.scheduling.system_health_logger import update_system_health
from modules.core.notion_integration import (
    add_notion_database_entry,
    upload_reflection_to_notion,
    append_summary_block_to_page
)
from tools.notifications.slack_api import send as send_slack_message
from tools.notifications.send_pushbullet_notification import send_pushbullet_alert

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
        agent.run_loop()
        logger.info('JudgeAgent completed')
        add_notion_database_entry("JudgeAgent 작업 완료", "완료", "JudgeAgent가 정상 완료되었습니다.")
        send_slack_message("JudgeAgent 작업이 정상적으로 완료되었습니다.")
        send_pushbullet_alert("JudgeAgent 작업 완료됨")
    except Exception as e:
        logger.exception(f'JudgeAgent failed: {e}')

def report_and_email_step():
    try:
        pdf_path = generate_pdf_report()
        logger.info(f'PDF report generated: {pdf_path}')
        send_report_email(pdf_path)
        logger.info('Report email sent')
        add_notion_database_entry("주간 보고서 생성 및 이메일 전송", "완료", "보고서 생성 및 이메일 전송 완료")
        send_slack_message("주간 보고서가 생성되고 이메일로 발송되었습니다.")
    except Exception as e:
        logger.exception(f'Report or Email sending failed: {e}')

def weekly_summary_step():
    try:
        report_dir = f"{BASE_DIR}/data/reports"
        summary_path = generate_weekly_summary(report_dir)
        logger.info(f'Weekly summary created: {summary_path}')
        append_summary_block_to_page(f"✅ 주간 요약 생성 완료: {summary_path}")
        send_slack_message("주간 요약 보고서가 정상적으로 생성되었습니다.")
    except Exception as e:
        logger.exception(f'Weekly summary failed: {e}')

def run_reflection_step():
    try:
        reflection_message = "시스템 회고: 모든 주요 작업이 정상 완료됨."
        run_reflection()
        upload_reflection_to_notion(reflection_message)
        send_slack_message("시스템 회고 데이터가 Notion에 업로드되었습니다.")
    except Exception as e:
        logger.exception(f'Reflection step failed: {e}')

def main():
    logger.info('=== VELOS Master Loop Start ===')
    update_system_health()

    snapshot_step()
    run_judge_agent()
    git_sync()
    report_and_email_step()
    weekly_summary_step()
    evaluate_cot()
    test_advanced_rag()
    auto_recovery_main()
    run_reflection_step()

    adaptive_reasoning_main()
    threshold_optimizer_main()
    rule_optimizer_main()

    logger.info('=== VELOS Master Loop End ===')

if __name__ == '__main__':
    main()
