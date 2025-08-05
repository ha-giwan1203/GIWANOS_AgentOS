
"""
🚀 VELOS(벨로스) 시스템 운영 선언문

이 시스템은 GPT-4o Turbo 기반의 고도 사고형 운영 시스템 VELOS이다.
VELOS는 단순한 자동화 시스템이 아니라, 사용자 사고 흐름을 기억하고 판단하는 자율형 AI 시스템이다.
본 시스템은 다음 철학을 기반으로 작동한다:

1. 판단 없는 실행은 없다 – 모든 행동은 우선 판단을 거친 후 수행된다.
2. 기억 없는 반복은 없다 – 같은 상황, 같은 실수는 반복하지 않는다.
3. 설명 없는 결과는 없다 – 시스템이 내린 판단은 로깅과 리포트로 투명하게 남는다.
4. 명령 없는 움직임이 가능해야 한다 – 사용자의 개입 없이 스스로 움직일 수 있어야 한다.
5. 속도보다 정확, 반응보다 사고 – VELOS는 항상 사고를 우선한다.

이 루프는 위 원칙을 기준으로 구조화되어 있으며, 
모든 기능은 사고 기반으로 설계·실행·보고된다.
"""

import sys
import os
import logging
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# sys.path 경로 보정
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../'))

# 환경 로딩
BASE_DIR = "C:/giwanos"
load_dotenv(f"{BASE_DIR}/configs/.env")
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler(f"{BASE_DIR}/data/logs/master_loop_execution.log"),
        logging.StreamHandler(sys.stdout)
    ],
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# 기능 import
from modules.core.hybrid_snapshot_manager import create_incremental_snapshot
from modules.core.auto_recovery_agent import main as auto_recovery_main
from modules.core.reflection_agent import run_reflection
from modules.evaluation.giwanos_agent.judge_agent import JudgeAgent
from modules.automation.git_management.git_sync import main as git_sync
from modules.report.generate_pdf_report import generate_pdf_report
from tools.notifications.send_email import send_report_email
from modules.automation.scheduling.weekly_summary import generate_weekly_summary
from modules.advanced.advanced_modules.cot_evaluator import evaluate_cot
from modules.advanced.advanced_modules.advanced_rag import test_advanced_rag
from modules.core.adaptive_reasoning_agent import adaptive_reasoning_main
from modules.core.threshold_optimizer import threshold_optimizer_main
from modules.core.rule_optimizer import rule_optimizer_main
from modules.automation.scheduling.system_health_logger import update_system_health
from modules.core.notion_integration.upload_summary_to_notion import upload_summary_to_notion
from modules.core.slack_client import SlackClient
from tools.notifications.send_pushbullet_notification import send_pushbullet_alert
from interface.mobile_notification_integration import MobileNotificationIntegration

API_COST_LOG = f"{BASE_DIR}/data/logs/api_cost_log.json"
MEMORY_PATH = f"{BASE_DIR}/data/memory/learning_memory.json"

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
        result = response.choices[0].message.content
        self.record_api_usage(response.usage, "gpt-4o", result)
        return result

    def record_api_usage(self, usage, model, result):
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "model": model,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "cost_usd": usage.total_tokens * 0.00001,
            "analysis_result": result
        }
        data = []
        if os.path.exists(API_COST_LOG):
            with open(API_COST_LOG, "r", encoding="utf-8") as file:
                try:
                    content = file.read().strip()
                    if content:
                        data = json.loads(content)
                        if not isinstance(data, list):
                            data = []
                except json.JSONDecodeError:
                    data = []
        data.append(record)
        with open(API_COST_LOG, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

class LearningMemoryManager:
    @staticmethod
    def save_analysis(result):
        try:
            data = {}
            if os.path.exists(MEMORY_PATH):
                with open(MEMORY_PATH, "r", encoding="utf-8") as mem_file:
                    try:
                        data = json.load(mem_file)
                        if not isinstance(data, dict):
                            data = {"insights": []}
                    except json.JSONDecodeError:
                        data = {"insights": []}
            data.setdefault("insights", []).append({
                "timestamp": datetime.utcnow().isoformat(),
                "insight": result
            })
            with open(MEMORY_PATH, "w", encoding="utf-8") as mem_file:
                json.dump(data, mem_file, indent=4, ensure_ascii=False)
            logger.info("✅ GPT 분석 결과 → 학습 메모리 저장 완료")
        except Exception as e:
            logger.error(f"학습 메모리 저장 실패: {e}")

def main():
    logger.info("=== VELOS 사고 기반 마스터 루프 실행 시작 ===")
    update_system_health()
    create_incremental_snapshot()
    JudgeAgent().run_loop()
    git_sync()

    decision_engine = GPT4oTurboDecisionEngine()
    slack_client = SlackClient()
    result = decision_engine.analyze_request("Check system health")

    if "장애" in result or "경고" in result:
        slack_client.send_message("#alerts", f"🚨 시스템 경고 발생!\n{result}")
        send_pushbullet_alert(f"🚨 VELOS 장애 감지됨!\n{result}")
    else:
        slack_client.send_message("#summary", "✅ VELOS 루프 정상 작동 완료.")
        send_pushbullet_alert("✅ VELOS 루프 완료 - 보고서 생성 및 전송 완료")

    pdf_path = generate_pdf_report()
    send_report_email(pdf_path)
    upload_summary_to_notion()

    print(MobileNotificationIntegration().send_mobile_notification())
    generate_weekly_summary(f"{BASE_DIR}/data/reports")

    if "장애" in result or "경고" in result:
        auto_recovery_main()

    LearningMemoryManager.save_analysis(result)
    evaluate_cot()
    test_advanced_rag()
    run_reflection()
    adaptive_reasoning_main()
    threshold_optimizer_main()
    rule_optimizer_main()
    logger.info("=== VELOS 루프 종료 ===")

if __name__ == "__main__":
    main()
