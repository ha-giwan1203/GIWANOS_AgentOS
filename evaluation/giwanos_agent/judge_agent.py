# C:/giwanos/evaluation/giwanos_agent/judge_agent.py

import os
import json
import shutil
from typing import Any, Dict

from core.auto_optimization_cleanup import main as cleanup_main
from notion_integration.notion_sync import main as notion_sync
from automation.git_management.git_sync import main as git_sync
from evaluation.human_readable_reports.generate_pdf_report import generate_pdf_report
from notifications.send_email import send_test_email as send_report_email
from evaluation.system.system_monitor import monitor_performance, check_memory_usage, disk_space_alert

class JudgeAgent:
    def __init__(self, config_path: str = "C:/giwanos/config/judgment_rules.json"):
        self.config_path = config_path
        self.tool_handlers: Dict[str, Any] = {
            "monitor_performance": monitor_performance,
            "check_memory_usage": lambda: check_memory_usage(),
            "disk_space_alert": lambda: disk_space_alert(),
        }
        self.judgment_rules = self.load_rules()

    def load_rules(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def run(self):
        # 1) 초기 진단
        self.run_diagnostics()

        # 2) 자동 최적화 및 클린업
        cleanup_main()
        # 3) Notion 동기화
        notion_sync()
        # 4) .tmp.driveupload 정리 및 GitSync
        shutil.rmtree("C:/giwanos/.tmp.driveupload", ignore_errors=True)
        git_sync()

        # 5) 시스템 인사이트 루프
        for action in ["monitor_performance", "check_memory_usage", "disk_space_alert"]:
            handler = self.tool_handlers.get(action)
            if handler:
                result = handler()
                if result:
                    print(f"[{action}] {result}")

        # 6) PDF 생성 및 이메일 전송
        generate_pdf_report()
        send_report_email()

    def run_diagnostics(self):
        print("[Diagnostics] 경로 및 JSON 파일 검증 진행 중...")