# =============================================================================
# 🧠 VELOS 시스템 철화 선언문
#
# 기억을 기반으로 구조적 생각을 수행하며,
# 판단 → 실행 → 회고 → 전송의 루프를 반복함으로써,
# 자신의 복구 가능한 자유 운영 AI 시스템을 지향한다.
# =============================================================================

import sys
sys.path.append("C:/giwanos")  # 바로 경로 설정

import os
import logging
from datetime import datetime
from pathlib import Path
import json

from modules.core.memory_reader import read_memory_context
from modules.core.context_aware_decision_engine import generate_gpt_response
from modules.automation.git_management.git_sync import sync_with_github
from modules.evaluation.giwanos_agent.judge_agent import run_judge_loop
from tools.notifications.send_email import send_email_report
from tools.notifications.send_pushbullet_notification import send_pushbullet_notification
from tools.notion_integration.upload_summary_to_notion import upload_summary_to_notion
from modules.core.reflection_agent import generate_reflection
from modules.evaluation.insight.system_insight_agent import run_insight_evaluation
from modules.core.threshold_optimizer import optimize_threshold
from modules.core.rule_optimizer import optimize_rules
from tools.chatbot_tools.automated_visualization_dashboard import generate_summary_dashboard
from modules.automation.update_system_health import update_system_health
from modules.evaluation.xai.models.xai_explanation_model import log_gpt_cost

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("data/logs/master_loop_execution.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def main():
    logging.info("=== VELOS 마스터 루프 시작 ===")
    print("\U0001f7e2 루프 시작: 시스템 상태 점검 및 스냅샷 생성")

    snapshot_dir = Path("C:/giwanos/data/snapshots")
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = snapshot_dir / f"incremental_snapshot_{datetime.now().strftime('%Y%m%d')}"
    snapshot_path.write_text("Incremental snapshot created", encoding="utf-8")
    print(f"\U0001f4f8 스냅샷 생성 완료 → {snapshot_path}")

    try:
        print("\U0001f9e0 JudgeAgent 실행")
        run_judge_loop()
        logging.info("✅ JudgeAgent 완료")
    except Exception as e:
        logging.error(f"JudgeAgent 실패: {e}")

    try:
        print("\U0001f501 GitHub 커밋 & 푸시 시작")
        sync_with_github()
        print("✅ GitHub 완료")
    except Exception as e:
        logging.error(f"GitHub 동기화 실패: {e}")

    try:
        print("\U0001f9e0 기억 로딩 및 context 생성 중...")
        context = read_memory_context()
        if not context:
            logging.warning("⚠️ context 불러오기 실패 → 기본 문구로 대체")
            context = "[기억 불러오기 실패 – 기본 프롬프트 사용]"

        user_request = "시스템 상태를 점검하고 요약해줘"
        full_prompt = f"{context}\n\n{user_request}"
        print("\U0001f9e0 GPT 판단 요청 전송 중...")
        gpt_response = generate_gpt_response(full_prompt)
    except Exception as e:
        logging.error(f"GPT 판단 생성 실패: {e}")
        gpt_response = "[GPT 판단 실패]"

    memory_path = Path("C:/giwanos/data/memory/learning_memory.json")
    memory_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(memory_path, "r", encoding="utf-8") as f:
            memory_data = json.load(f)
    except:
        memory_data = {}

    if "insights" not in memory_data:
        memory_data["insights"] = []

    memory_data["insights"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "from": "user",
        "insight": user_request,
        "tags": ["요청", "점검"]
    })
    memory_data["insights"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "from": "system",
        "insight": gpt_response,
        "tags": ["판단", "GPT"]
    })

    try:
        with open(memory_path, "w", encoding="utf-8") as f:
            json.dump(memory_data, f, indent=2, ensure_ascii=False)
        print(f"\U0001f9e0 메모리에 저장됨 → {gpt_response[:40]}...")
    except Exception as e:
        logging.error(f"메모리 저장 실패: {e}")

    for label, func in [
        ("update_system_health", update_system_health),
        ("generate_summary_dashboard", generate_summary_dashboard),
        ("log_gpt_cost", lambda: log_gpt_cost(gpt_response)),
        ("send_email_report", lambda: send_email_report("VELOS 리포트", "보고서 전송", "you@example.com")),
        ("send_pushbullet_notification", lambda: send_pushbullet_notification("VELOS", "보고서 전송 완료됨.")),
        ("upload_summary_to_notion", upload_summary_to_notion),
        ("generate_reflection", generate_reflection),
        ("run_insight_evaluation", run_insight_evaluation),
        ("optimize_threshold", optimize_threshold),
        ("optimize_rules", optimize_rules)
    ]:
        try:
            print(f"▶️ {label} 실행 중...")
            func()
            print(f"✅ {label} 완료")
        except Exception as e:
            logging.error(f"❌ {label} 실패: {e}")

    logging.info("=== VELOS 마스터 루프 종료 ===")
    print("🏁 루프 종료")

if __name__ == "__main__":
    main()
