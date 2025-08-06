# =============================================================================
# 🧠 VELOS 시스템 철학 선언문
#
# 기억을 기반으로 구조적 사고를 수행하며,
# 판단 → 실행 → 회고 → 전송의 루프를 반복함으로써,
# 스스로 개선되는 자율 운영 AI 시스템을 지향한다.
# =============================================================================

import sys
sys.path.append("C:/giwanos")

import os
import logging
from datetime import datetime
from pathlib import Path
import json
import zipfile

from modules.core.memory_reader import read_memory_context
from modules.core.context_aware_decision_engine import generate_gpt_response
from modules.automation.git_management.git_sync import sync_with_github
from modules.evaluation.giwanos_agent.judge_agent import run_judge_loop
from tools.notifications.send_email import send_email_report
from tools.notifications.send_pushbullet_notification import send_pushbullet_notification
from tools.notifications.slack_api import send_slack_message
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

def save_insight_report(text):
    report_dir = Path("C:/giwanos/data/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    file_path = report_dir / f"ai_insight_{datetime.now().strftime('%Y%m%d')}.md"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"✅ GPT 판단 보고서 저장 완료 → {file_path}")

def save_reflection_log():
    reflection_path = Path("C:/giwanos/data/reports/reflection_log")
    reflection_path.mkdir(parents=True, exist_ok=True)
    file_path = reflection_path / f"reflection_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    result = generate_reflection()
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"✅ 회고 저장 완료 → {file_path}")

def zip_all_reports():
    export_dir = Path("C:/giwanos/data/exports")
    export_dir.mkdir(parents=True, exist_ok=True)
    zip_path = export_dir / f"VELOS_report_{datetime.now().strftime('%Y%m%d')}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        report_root = Path("C:/giwanos/data/reports")
        for path in report_root.rglob("*.*"):
            zipf.write(path, arcname=path.relative_to(report_root.parent))

    print(f"📦 보고서 ZIP 압축 완료 → {zip_path}")

def track_loop_status(start_time, success, failed_steps, summary):
    log_path = Path("C:/giwanos/data/logs/loop_state_tracker.json")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "started_at": start_time.isoformat(),
        "ended_at": datetime.utcnow().isoformat(),
        "status": "success" if success else "failure",
        "failed_steps": failed_steps,
        "summary": summary[:200]  # 일부만 저장
    }

    try:
        if log_path.exists():
            with open(log_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        else:
            history = []
        history.append(record)
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print(f"🗂 루프 실행 상태 저장 완료 → {log_path}")
    except Exception as e:
        print(f"❌ 루프 상태 저장 실패: {e}")

def main():
    start_time = datetime.utcnow()
    failed_steps = []
    summary_text = ""

    logging.info("=== VELOS 마스터 루프 시작 ===")
    print("🟢 루프 시작: 시스템 상태 점검 및 스냅샷 생성")

    snapshot_dir = Path("C:/giwanos/data/snapshots")
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = snapshot_dir / f"incremental_snapshot_{datetime.now().strftime('%Y%m%d')}"
    snapshot_path.write_text("Incremental snapshot created", encoding="utf-8")
    print(f"📸 스냅샷 생성 완료 → {snapshot_path}")

    try:
        print("🧠 JudgeAgent 실행")
        run_judge_loop()
        logging.info("✅ JudgeAgent 완료")
    except Exception as e:
        logging.error(f"JudgeAgent 실패: {e}")
        failed_steps.append("judge_agent")

    try:
        print("🔁 GitHub 커밋 & 푸시 시작")
        sync_with_github()
        print("✅ GitHub 완료")
    except Exception as e:
        logging.error(f"GitHub 동기화 실패: {e}")
        failed_steps.append("git_sync")

    try:
        print("🧠 기억 로딩 및 context 생성 중...")
        context = read_memory_context()
        if not context:
            logging.warning("⚠️ context 불러오기 실패 → 기본 문구로 대체")
            context = "[기억 불러오기 실패 – 기본 프롬프트 사용]"

        user_request = "시스템 상태를 점검하고 요약해줘"
        full_prompt = f"{context}\n\n{user_request}"
        print("🧠 GPT 판단 요청 전송 중...")
        gpt_response = generate_gpt_response(full_prompt)
        summary_text = gpt_response
        save_insight_report(gpt_response)
    except Exception as e:
        logging.error(f"GPT 판단 생성 실패: {e}")
        gpt_response = "[GPT 판단 실패]"
        failed_steps.append("gpt_decision")

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
        print(f"🧠 메모리에 저장됨 → {gpt_response[:40]}...")
    except Exception as e:
        logging.error(f"메모리 저장 실패: {e}")
        failed_steps.append("memory_save")

    to_email = os.getenv("EMAIL_TO")
    print("[이메일 전송 테스트] 받는 사람:", to_email)

    steps = [
        ("update_system_health", update_system_health),
        ("generate_summary_dashboard", generate_summary_dashboard),
        ("log_gpt_cost", lambda: log_gpt_cost(gpt_response)),
        ("send_email_report", lambda: send_email_report("VELOS 시스템 리포트", "보고서 자동 전송입니다.", to_email)),
        ("send_pushbullet_notification", lambda: send_pushbullet_notification("VELOS", "보고서 전송 완료됨.")),
        ("send_slack_message", lambda: send_slack_message("📡 VELOS 보고서가 자동 생성되었습니다.")),
        ("upload_summary_to_notion", lambda: upload_summary_to_notion(summary_path="C:/giwanos/data/reports/summary_dashboard.json")),
        ("generate_reflection", save_reflection_log),
        ("run_insight_evaluation", run_insight_evaluation),
        ("optimize_threshold", optimize_threshold),
        ("optimize_rules", optimize_rules),
        ("zip_all_reports", zip_all_reports)
    ]

    for label, func in steps:
        try:
            print(f"▶️ {label} 실행 중...")
            func()
            print(f"✅ {label} 완료")
        except Exception as e:
            logging.error(f"❌ {label} 실패: {e}")
            failed_steps.append(label)

    track_loop_status(start_time, len(failed_steps) == 0, failed_steps, summary_text)

    logging.info("=== VELOS 마스터 루프 종료 ===")
    print("🏁 루프 종료")

if __name__ == "__main__":
    main()
