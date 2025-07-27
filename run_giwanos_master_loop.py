import sys
import os
from core.controller import Controller
from core.hybrid_snapshot_manager import manage_snapshots
from core.reflection_agent import ReflectionAgent
from core.auto_optimization_cleanup import main as optimize_and_cleanup
from core.system_integrity_check import main as system_check
from evaluation.human_readable_reports.generate_pdf_report import generate_and_send_report
from notion_integration.notion_sync import main as notion_sync
from automation.git_management.git_sync import git_sync  # import the function directly

os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

import logging
logging.basicConfig(
    level=logging.ERROR,
    filename="C:/giwanos/data/logs/master_loop_execution.log",
    format='%(asctime)s %(levelname)s %(message)s',
    encoding='utf-8'
)

def master_loop():
    try:
        print("[1] 시스템 자기 진단 시작")
        system_check()

        print("[2] Controller 생성 및 실행")
        controller = Controller()
        controller.run()

        print("[3] Reflection 파일 생성")
        reflection_agent = ReflectionAgent()
        reflection_agent.create_reflection()

        print("[4] 자동 최적화 및 클린업 실행")
        optimize_and_cleanup()

        print("[5] 하이브리드 스냅샷 생성")
        manage_snapshots()

        print("[6] 보고서 생성 및 이메일 전송")
        generate_and_send_report()

        print("[7] Notion 동기화 실행")
        notion_sync()

        print("[8] GitHub 동기화 실행")
        git_sync()

        print("[✅ GIWANOS 시스템 전체 마스터 루프 성공]")

    except Exception as e:
        error_message = f"[❌ GIWANOS 시스템 전체 마스터 루프 오류]: {str(e)}"
        print(error_message)
        logging.error(error_message)

if __name__ == "__main__":
    master_loop()
