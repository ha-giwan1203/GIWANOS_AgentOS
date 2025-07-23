# report_agent.py
from giwanos_agent.base_agent import BaseAgent
from typing import Any
import os
import json

class ReportAgent(BaseAgent):
    def execute(self, reflection_path: str) -> None:
        print("✅ report_agent 실행됨!")
        with open(reflection_path, "r", encoding="utf-8") as f:
            content = f.read()

        report_dir = "reports"
        os.makedirs(report_dir, exist_ok=True)
        saved_path = os.path.join(report_dir, os.path.basename(reflection_path))
        with open(saved_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📄 보고서 저장됨: {saved_path}")

        try:
            from upload_notion_safe import send_to_notion
            send_to_notion(saved_path)
            print("✅ Notion 전송 완료")
        except Exception as e:
            print("⚠️ Notion 전송 실패 또는 모듈 없음:", e)

def run():
    agent = ReportAgent()
    test_md_path = "reflections/loop_reflection_log_dummy.md"
    if not os.path.exists(test_md_path):
        with open(test_md_path, "w", encoding="utf-8") as f:
            f.write("# Dummy Reflection\n\n- Example content")
    agent.execute(test_md_path)
