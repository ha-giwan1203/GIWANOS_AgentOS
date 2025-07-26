try:
    from core.judge_agent import JudgeAgent
except ModuleNotFoundError:
    from core.judge_agent import JudgeAgent

class Controller:
    def __init__(self):
        self.agent = JudgeAgent()

    def run(self):
        self.agent.execute()