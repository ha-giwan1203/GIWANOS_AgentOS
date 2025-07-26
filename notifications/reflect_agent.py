# reflect_agent.py
from giwanos_agent.base_agent import BaseAgent
from typing import Dict, Any
import datetime
import os

class ReflectAgent(BaseAgent):
    def execute(self, loop_result: Dict[str, Any]) -> str:
        print("✅ reflect_agent 실행됨!")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reflections/loop_reflection_log_{timestamp}.md"
        os.makedirs("reflections", exist_ok=True)
        content = f"# 회고 리포트\n\n{loop_result}\n"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📄 회고 저장됨: {filename}")
        return filename

def run():
    agent = ReflectAgent()
    agent.execute({"dummy": "loop result for testing"})
