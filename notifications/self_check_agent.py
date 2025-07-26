# self_check_agent.py
from giwanos_agent.base_agent import BaseAgent
from typing import Any, Dict
import json
import os

class SelfCheckAgent(BaseAgent):
    def execute(self, _: Any) -> Dict[str, Any]:
        print("✅ self_check_agent 실행됨!")
        path = "memory_status.json"
        if not os.path.exists(path):
            return {"status": "error", "message": "memory_status.json 없음"}
        with open(path, encoding="utf-8") as f:
            status = json.load(f)
        if not status.get("status_ok", True):
            print("⚠️ 메모리 이상 감지됨:", status)
        else:
            print("✅ 메모리 상태 양호")
        return status

def run():
    agent = SelfCheckAgent()
    agent.execute({})
