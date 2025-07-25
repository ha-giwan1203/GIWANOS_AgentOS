import logging
import os
from giwanos_agent.reflection_agent import ReflectionAgent

log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'agent_logs'))
os.makedirs(log_dir, exist_ok=True)

logger = logging.getLogger('judge_agent_logger')
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(os.path.join(log_dir, 'judge_agent.log'), encoding='utf-8')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

class JudgeAgent:
    def __init__(self):
        logger.info("JudgeAgent initialized.")
        self.reflection_agent = ReflectionAgent()

    def execute(self):
        logger.info("Executing JudgeAgent detailed logic.")
        self.reflection_agent.create_reflection()
        logger.info("Reflection created successfully.")

    def run_loop(self):
        logger.info("Starting JudgeAgent run loop.")
        self.execute()
        logger.info("Run loop completed.")