import sys
from judge_agent import JudgeAgent

def main(mode="auto"):
    agent = JudgeAgent()
    if mode == "auto":
        agent.run()
    elif mode == "plan":
        agent.plan()
    else:
        print(f"Unknown mode: {mode}")

if __name__ == "__main__":
    mode = "auto"
    if len(sys.argv) > 1:
        mode = sys.argv[1]

    print(f"Running JudgeAgent controller in {mode} mode.")
    main(mode)
