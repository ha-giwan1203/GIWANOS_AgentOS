
import logging
import subprocess
import os

logging.basicConfig(level=logging.INFO)

class JudgeAgent:
    def __init__(self):
        logging.info("JudgeAgent initialized.")

    def execute_reflection_logic(self):
        logging.info("Executing Reflection logic.")
        logging.info("Reflection created successfully.")

    def execute_failure_detection(self):
        subprocess.run(["python", "C:/giwanos/core/system_failure_detector.py"], check=True)

    def execute_auto_recovery(self):
        subprocess.run(["python", "C:/giwanos/core/auto_recovery_agent.py"], check=True)

    def execute_ai_evaluation_and_report(self):
        subprocess.run(["python", "C:/giwanos/evaluation/ai_reports/generate_ai_insight_report.py"], check=True)
        subprocess.run(["python", "C:/giwanos/evaluation/ai_reports/insights_to_report.py"], check=True)

    def run(self):
        logging.info("JudgeAgent 루프 시작")
        self.execute_reflection_logic()
        self.execute_failure_detection()
        self.execute_auto_recovery()
        self.execute_ai_evaluation_and_report()
        logging.info("JudgeAgent 루프 완료")

if __name__ == "__main__":
    agent = JudgeAgent()
    agent.run()
