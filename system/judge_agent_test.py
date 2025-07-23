
from giwanos_agent.judge_agent import JudgeAgent

def run_test_case(mode, parameters=None):
    print("\n🧪 JudgeAgent 루프 테스트 시작\n")
    agent = JudgeAgent()  # 인스턴스 생성
    try:
        print(f"▶ 테스트 시작: {mode}")
        result = agent.run_loop(mode, parameters or {})
        print("✅ 결과:")
        print(result)
    except Exception as e:
        print("❌ 예외 발생:")
        print(e)
    print("⏹ 테스트 완료\n")

if __name__ == "__main__":
    run_test_case("전체 루프 실행")
    run_test_case("정리만")
