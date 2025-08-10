
from core.judge_agent import JudgeAgent
from core.gpt import GPT  # 정확한 경로로 수정 완료

class Controller:
    def __init__(self):
        gpt_instance = GPT(api_key="사용자_API_키")
        self.agent = JudgeAgent(gpt_instance)

    def run(self):
        self.agent.run()

if __name__ == "__main__":
    controller = Controller()
    controller.run()


