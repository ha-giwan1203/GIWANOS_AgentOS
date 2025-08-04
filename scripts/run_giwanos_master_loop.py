
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

# 환경변수 로드
load_dotenv(f"{BASE_DIR}/configs/.env")

# OpenAI 클라이언트 초기화
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 주요 경로
API_COST_LOG = f"{BASE_DIR}/data/logs/api_cost_log.json"
MEMORY_PATH = f"{BASE_DIR}/data/memory/learning_memory.json"

# 모듈 import
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

# GPT 분석 엔진
class GPT4oTurboDecisionEngine:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "model": model_name,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "cost_usd": usage.total_tokens * 0.00001,
            "analysis_result": analysis_result
        }

        data = []
        if os.path.exists(API_COST_LOG):
            with open(API_COST_LOG, 'r', encoding='utf-8') as file:
                try:
                    file_content = file.read().strip()
                    if file_content:
                        data = json.loads(file_content)
                        if not isinstance(data, list):
                            data = []
                except json.JSONDecodeError:
                    data = []

        data.append(record)

        with open(API_COST_LOG, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

# 메모리 저장기
class LearningMemoryManager:
    @staticmethod
    def save_analysis(analysis_result):
        try:
            data = {}
            if os.path.exists(MEMORY_PATH):
                with open(MEMORY_PATH, 'r', encoding='utf-8') as mem_file:
                    try:
                        data = json.load(mem_file)
                        if not isinstance(data, dict):
                            data = {"insights": []}
                    except json.JSONDecodeError:
                        data = {"insights": []}

            data.setdefault("insights", []).append({
                "timestamp": datetime.utcnow().isoformat(),
                "insight": analysis_result
            })

            with open(MEMORY_PATH, 'w', encoding='utf-8') as mem_file:
                json.dump(data, mem_file, indent=4, ensure_ascii=False)

            logger.info("✅ 학습 메모리에 GPT-4o Turbo 분석 결과 저장 완료")

        except Exception as e:
            logger.error(f"학습 메모리 업데이트 실패: {e}")

def main():
    logger.info('=== VELOS Master Loop Start ===')
    update_system_health()

    create_incremental_snapshot()
    JudgeAgent().run_loop()
    git_sync()

    decision_engine = GPT4oTurboDecisionEngine()
    slack_client = SlackClient()
    analysis_result = decision_engine.analyze_request("Check system health")

    # 조건부 Slack 알림
    if "장애" in analysis_result or "경고" in analysis_result:
        slack_client.send_message("#alerts", f"🚨 시스템 경고 발생!\n{analysis_result}")
    else:
        slack_client.send_message("#summary", "✅ VELOS 루프 정상 작동 완료.")

    pdf_report_path = generate_pdf_report()
    send_report_email(pdf_report_path)
    generate_weekly_summary(f"{BASE_DIR}/data/reports")

    if "장애" in analysis_result or "경고" in analysis_result:
        auto_recovery_main()

    LearningMemoryManager.save_analysis(analysis_result)

    evaluate_cot()
    test_advanced_rag()
    run_reflection()
    adaptive_reasoning_main()
    threshold_optimizer_main()
    rule_optimizer_main()

    logger.info('=== VELOS Master Loop End ===')

if __name__ == "__main__":
    main()
