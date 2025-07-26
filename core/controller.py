
from core.judge_agent import JudgeAgent

class Controller:
    def __init__(self):
        self.agent = JudgeAgent()

    def run(self):
        self.agent.run()

if __name__ == "__main__":
    controller = Controller()
    controller.run()
