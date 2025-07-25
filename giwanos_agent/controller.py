try:
    from giwanos_agent.judge_agent import JudgeAgent
except ModuleNotFoundError:
    from judge_agent import JudgeAgent

class Controller:
    def __init__(self):
        self.agent = JudgeAgent()

    def run(self):
        self.agent.execute()