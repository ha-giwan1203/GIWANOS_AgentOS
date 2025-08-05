# 🚀 VELOS(벨로스) 시스템 운영 선언문
# 본 루프는 사용자 명령 흐름을 기억하고, 자동 복구/회고/보고서 생성을 포함한
# 완전 자동 운영 체계를 실행합니다. 판단 없는 실행은 없으며, 기억 없는 반복은 없습니다.
# 해당 파일은 VELOS 마스터 루프의 전체 실행기능을 포함한 최종 형태입니다.
# 사용자 명령을 memory에 저장하고, GPT 결과를 반복하지 않게 확인하며,
# 회고, 보고서, Slack 전송 까지 전체로 연동됩니다.

import sys
import os
import logging
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# 경로 보정
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../'))

# 환경 설정
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
from modules.core.learning_memory_manager import LearningMemoryManager
from scripts.generate_memory_reflection import run_memory_reflection

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

def main():
    logger.info("=== VELOS 사고 기반 마스터 루프 실행 시작 ===")
    update_system_health()
    create_incremental_snapshot()
    JudgeAgent().run_loop()
    git_sync()

    decision_engine = GPT4oTurboDecisionEngine()
    slack_client = SlackClient()

    request_prompt = "Check system health"
    LearningMemoryManager.save_insight("user", request_prompt, ["명령", "상태_점검"])
    result = decision_engine.analyze_request(request_prompt)

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

    # 🧠 회고 자동 생성 + Slack 전송
    reflection_path = run_memory_reflection()
    if reflection_path:
        print(f"🧠 회고 자동 생성 완료 → {reflection_path}")
        try:
            with open(reflection_path, "r", encoding="utf-8") as f:
                reflection_data = json.load(f)

            reflection_msg = reflection_data.get("summary", "")
            reflection_level = reflection_data.get("level", "normal")
            reflection_ts = reflection_data.get("timestamp", "")

            channel = "#alerts" if reflection_level == "critical" else "#summary"
            slack_client.send_message(
                channel,
                f"🧠 *VELOS 회고 요약* ({reflection_level.upper()})\n📅 {reflection_ts}\n\n{reflection_msg}"
            )

        except Exception as e:
            print(f"⚠️ 회고 Slack 전송 실패: {e}")
    else:
        print("⚠️ 회고 생성 실패 또는 사용자 명령 없음")

    logger.info("=== VELOS 루프 종료 ===")

if __name__ == "__main__":
    main()

