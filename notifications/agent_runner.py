# agent_runner.py
import argparse
from giwanos.reporting.agent_logger import save_agent_status

from giwanos.reflection import judge_agent
from giwanos import reflect_agent, report_agent, self_check_agent
from giwanos.memory import loop_recommender_memory

AGENTS = {
    "judge": judge_agent.run,
    "reflect": reflect_agent.run,
    "report": report_agent.run,
    "recommend": loop_recommender_memory.run,
    "selfcheck": self_check_agent.run
}

def run_all():
    print("🔁 모든 에이전트 실행 시작")
    for name, func in AGENTS.items():
        try:
            print(f"▶ 에이전트 실행: {name}")
            func()
            save_agent_status(name, "success")
        except Exception as e:
            print(f"❌ {name} 실패: {e}")
            save_agent_status(name, "failed", {"error": str(e)})
    print("✅ 전체 에이전트 실행 완료")

def run_single(agent_name):
    if agent_name not in AGENTS:
        raise ValueError(f"❌ 지원하지 않는 에이전트: {agent_name}")
    print(f"▶ 에이전트 실행: {agent_name}")
    try:
        AGENTS[agent_name]()
        save_agent_status(agent_name, "success")
    except Exception as e:
        print(f"❌ {agent_name} 실패: {e}")
        save_agent_status(agent_name, "failed", {"error": str(e)})

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GIWANOS 에이전트 실행기")
    parser.add_argument("--agent", type=str, help="실행할 에이전트 이름 (생략 시 전체 실행)")
    args = parser.parse_args()

    if args.agent:
        run_single(args.agent)
    else:
        run_all()
