# =============================================
# VELOS 운영 철학 선언문
# 본 스크립트는 VELOS 시스템의 마스터 루프를 실행하며,
# 자가 진단, 자동 보고서 생성, 연동 시스템 알림을 통합 수행합니다.
# 파일명은 절대 변경하지 않으며, 모든 흐름은 기억과 판단에 기반합니다.
# =============================================

import sys, os, logging, json
from datetime import datetime
import openai
from dotenv import load_dotenv

sys.path.append("C:/giwanos")

BASE_DIR = "C:/giwanos"
load_dotenv(f"{BASE_DIR}/configs/.env")
openai.api_key = os.getenv("OPENAI_API_KEY")

# 경로 설정
JUDGMENT_INDEX_PATH = f"{BASE_DIR}/data/judgments/judgment_history_index.json"
DIALOG_MEMORY_PATH = f"{BASE_DIR}/data/memory/dialog_memory.json"
API_COST_LOG = f"{BASE_DIR}/data/logs/api_cost_log.json"
LOG_PATH = f"{BASE_DIR}/data/logs/master_loop_execution.log"

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler(sys.stdout)],
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# 🔧 올바른 import 구문 (기준 구조 기준)
from modules.core.slack_client import SlackClient
from tools.notifications.send_pushbullet_notification import send_pushbullet_notification
from tools.notifications.send_email import send_report_email
from modules.report.generate_pdf_report import generate_pdf_report
from tools.notion_integration.upload_summary_to_notion import upload_summary_to_notion
from modules.automation.scheduling.weekly_summary import generate_weekly_summary
from modules.automation.scheduling.system_health_logger import update_system_health
from modules.core.auto_recovery_agent import main as auto_recovery_main
from modules.core.reflection_agent import run_reflection
from modules.evaluation.giwanos_agent.judge_agent import JudgeAgent
from modules.automation.git_management.git_sync import main as git_sync
from modules.advanced.advanced_modules.cot_evaluator import evaluate_cot
from modules.advanced.advanced_modules.advanced_rag import test_advanced_rag
from modules.core.adaptive_reasoning_agent import adaptive_reasoning_main
from modules.core.threshold_optimizer import threshold_optimizer_main
from modules.core.rule_optimizer import rule_optimizer_main

class GPT4oTurboDecisionEngine:
    def __init__(self):
        pass

    def analyze_request(self, request):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "GPT-4 Turbo AI Judge"},
                    {"role": "user", "content": request}
                ]
            )
            result = response['choices'][0]['message']['content']
            self.record_api_usage(response['usage'], "gpt-4", result)
            return result
        except Exception as e:
            logger.error(f"OpenAI API 호출 실패: {e}")
            return "Error occurred during request analysis."

    def record_api_usage(self, usage, model, result):
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "model": model,
            "prompt_tokens": usage['prompt_tokens'],
            "completion_tokens": usage['completion_tokens'],
            "total_tokens": usage['total_tokens'],
            "cost_usd": usage['total_tokens'] * 0.00001,
            "analysis_result": result
        }
        data = []
        if os.path.exists(API_COST_LOG):
            with open(API_COST_LOG, "r", encoding="utf-8") as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    data = []
        data.append(record)
        with open(API_COST_LOG, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

def save_dialog_memory(message):
    entry = {
        "session_id": datetime.utcnow().strftime("%Y%m%d_%H%M%S"),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "conversations": [{
            "role": "system",
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }]
    }
    if os.path.exists(DIALOG_MEMORY_PATH):
        with open(DIALOG_MEMORY_PATH, "r", encoding="utf-8") as f:
            try:
                dialog_memory = json.load(f)
            except json.JSONDecodeError:
                dialog_memory = {"sessions": []}
    else:
        dialog_memory = {"sessions": []}
    dialog_memory["sessions"].append(entry)
    with open(DIALOG_MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(dialog_memory, f, ensure_ascii=False, indent=2)
    logger.info("✅ 메모리 누적 저장 완료")

def save_judgment(result):
    judgment = {
        "id": datetime.utcnow().strftime("%Y%m%d_%H%M%S"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "user_request": "Check system health",
        "explanation": result,
        "tags": ["운영"]
    }
    judgments = []
    if os.path.exists(JUDGMENT_INDEX_PATH):
        with open(JUDGMENT_INDEX_PATH, "r", encoding="utf-8") as f:
            try:
                judgments = json.load(f)
            except json.JSONDecodeError:
                judgments = []
    judgments.append(judgment)
    with open(JUDGMENT_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(judgments, f, ensure_ascii=False, indent=2)
    logger.info("✅ 판단 데이터 누적 저장 완료")

def main():
    logger.info("=== VELOS 통합 마스터 루프 시작 ===")

    update_system_health()
    git_sync()
    JudgeAgent().run_loop()

    decision_engine = GPT4oTurboDecisionEngine()
    slack_client = SlackClient()
    request = "Check system health"
    result = decision_engine.analyze_request(request)

    save_dialog_memory(result)
    save_judgment(result)

    pdf_report_path = generate_pdf_report()
    send_report_email(pdf_report_path)
    upload_summary_to_notion()

    if "장애" in result or "경고" in result:
        slack_client.send_message("#alerts", f"🚨 시스템 경고 발생!\n{result}")
        send_pushbullet_notification("🚨 VELOS 장애 감지됨!", result)
        auto_recovery_main()
    else:
        slack_client.send_message("#summary", "✅ VELOS 루프 정상 작동 완료.")
        send_pushbullet_notification("✅ VELOS 루프 완료", "보고서 생성 및 전송 완료")

    evaluate_cot()
    test_advanced_rag()
    adaptive_reasoning_main()
    threshold_optimizer_main()
    rule_optimizer_main()
    run_reflection()

    generate_weekly_summary(f"{BASE_DIR}/data/reports")

    logger.info("=== VELOS 통합 마스터 루프 종료 ===")

if __name__ == "__main__":
    main()
