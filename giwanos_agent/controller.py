
# controller.py
from judge_agent import JudgeAgent
import sys

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "auto"
    agent = JudgeAgent()
    agent.initialize()
    result = agent.run_plan_and_execute(mode)
    print(f"[Controller] 실행 결과:\n{result}")

if __name__ == "__main__":
    main()
