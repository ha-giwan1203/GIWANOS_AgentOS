
from giwanos_agent.controller import JudgeAgent

def main():
    agent = JudgeAgent()
    agent.run_reflection()
    print("✅ GIWANOS 회고 루프 실행 완료")

if __name__ == "__main__":
    main()
