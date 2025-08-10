"""
File: C:/giwanos/core/controller.py

설명:
- Controller 클래스: JudgeAgent 인스턴스를 composition으로 보유
- JudgeAgent.__init__ 호출 시 인자 없이 생성
"""

from core.judge_agent import JudgeAgent

class Controller:
    def __init__(self):
        # JudgeAgent 기본 생성자 사용
        self.agent = JudgeAgent()

    def run(self):
        # Agent의 run 메서드 호출
        self.agent.run()


