import logging
import sys
import os
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# 경로 설정
BASE_DIR = "C:/giwanos"
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

# 환경변수 로딩
load_dotenv("C:/giwanos/configs/.env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 모듈 임포트
from modules.core.hybrid_snapshot_manager import create_incremental_snapshot
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
from modules.core.slack_client import SlackClient

# GPT-4o Turbo Decision Engine
class GPT4oTurboDecisionEngine:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def analyze_request(self, request):
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "GPT-4o Turbo API Call"},
                {"role": "user", "content": request}
            ]
        )
        analysis_result = response.choices[0].message.content
        self.record_api_usage(response.usage, "gpt-4o", analysis_result)
        return analysis_result

    def record_api_usage(self, usage, model_name, analysis_result):
        log_path = f"{BASE_DIR}/data/logs/api_cost_log.json"
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "model": model_name,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "cost_usd": usage.total_tokens * 0.00001,
            "analysis_result": analysis_result
        }

        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as file:
                data = json.load(file) if file.read().strip() else []
        else:
            data = []

        data.append(record)

        with open(log_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

# Learning Memory Manager
class LearningMemoryManager:
    MEMORY_PATH = f"{BASE_DIR}/data/memory/learning_memory.json"

    @staticmethod
    def save_analysis(analysis_result):
        with open(LearningMemoryManager.MEMORY_PATH, 'r+', encoding='utf-8') as mem_file:
            memory_data = json.load(mem_file)
            memory_data["insights"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "insight": analysis_result
            })
            mem_file.seek(0)
            json.dump(memory_data, mem_file, indent=4, ensure_ascii=False)

def main():
    logger.info('=== VELOS Master Loop Start ===')
    update_system_health()
    create_incremental_snapshot()

    JudgeAgent().run_loop()
    git_sync()

    decision_engine = GPT4oTurboDecisionEngine()
    slack_client = SlackClient()

    analysis_result = decision_engine.analyze_request("Check system health")
    slack_result = slack_client.send_message("#general", analysis_result)
    logger.info(f"Slack 알림 전송 결과: {slack_result}")

    # 보고서 및 이메일 발송
    pdf_path = generate_pdf_report()
    send_report_email(pdf_path)
    weekly_summary = generate_weekly_summary(f"{BASE_DIR}/data/reports")

    # Notion 알림 추가
    add_notion_database_entry("GPT-4o 분석 결과", "완료", analysis_result)
    append_summary_block_to_page(f"✅ 주간 요약 생성 완료: {weekly_summary}")
    upload_reflection_to_notion("시스템 회고: 모든 주요 작업이 정상 완료됨.")

    # 분석 결과 메모리에 저장
    LearningMemoryManager.save_analysis(analysis_result)
    logger.info(f"GPT-4o 분석 결과 메모리에 저장 완료: {analysis_result}")

    evaluate_cot()
    test_advanced_rag()
    auto_recovery_main()
    run_reflection()
    adaptive_reasoning_main()
    threshold_optimizer_main()
    rule_optimizer_main()

    logger.info('=== VELOS Master Loop End ===')

if __name__ == '__main__':
    main()
