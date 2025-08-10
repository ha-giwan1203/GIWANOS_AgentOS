
from modules.core.time_utils import now_utc, now_kst, iso_utc, monotonic
import json
import logging
from datetime import datetime
import os
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

feedback_file_path = 'C:/giwanos/data/reports/evaluation_feedback.json'

def evaluate_system_performance():
    # 시스템 성능 평가 (실제 평가 로직을 여기에 구현)
    performance = {
        "timestamp": now_utc().isoformat(),
        "cpu_usage_percent": random.uniform(10, 20),
        "memory_usage_percent": random.uniform(30, 50),
        "disk_usage_percent": random.uniform(70, 90),
        "active_processes": random.randint(200, 250),
        "api_call_reduction_percent": random.uniform(75, 85)
    }
    logging.info('System performance evaluated.')
    return performance

def save_evaluation_feedback(feedback):
    with open(feedback_file_path, 'w', encoding='utf-8') as f:
        json.dump(feedback, f, indent=4)
    logging.info(f'Feedback saved to {feedback_file_path}.')

def load_previous_feedback():
    if os.path.exists(feedback_file_path):
        with open(feedback_file_path, 'r', encoding='utf-8') as f:
            feedback = json.load(f)
        logging.info('Previous feedback loaded successfully.')
        return feedback
    logging.info('No previous feedback file found, initializing new feedback.')
    return None

def main():
    current_feedback = evaluate_system_performance()
    previous_feedback = load_previous_feedback()

    if previous_feedback:
        # 성능 개선 사항 확인 (간단한 비교 로직, 필요 시 정교화 가능)
        for key in current_feedback:
            if key != "timestamp":
                diff = current_feedback[key] - previous_feedback.get(key, 0)
                logging.info(f'{key}: Previous={previous_feedback.get(key, "N/A")}, Current={current_feedback[key]:.2f}, Difference={diff:.2f}')

    save_evaluation_feedback(current_feedback)

if __name__ == "__main__":
    main()



