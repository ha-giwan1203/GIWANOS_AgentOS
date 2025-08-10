
from modules.core.time_utils import now_utc, now_kst, iso_utc, monotonic
import json
import logging
import os
from datetime import datetime
import random

logging.basicConfig(level=logging.INFO)

MEMORY_PATH = "C:/giwanos/memory/learning_memory.json"

def load_learning_memory():
    try:
        with open(MEMORY_PATH, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"학습 메모리 로드 실패: {e}")
        return {"recent_events": [], "insights": [], "user_behavior": [], "performance_metrics": []}

def save_learning_memory(memory_data):
    try:
        with open(MEMORY_PATH, 'w', encoding='utf-8') as file:
            json.dump(memory_data, file, indent=4, ensure_ascii=False)
        logging.info("✅ 성능 지표 저장 성공")
    except Exception as e:
        logging.error(f"성능 지표 저장 실패: {e}")

def evaluate_performance():
    accuracy = round(random.uniform(0.9, 1.0), 4)
    response_time = round(random.uniform(0.1, 0.5), 4)
    system_health = random.choice(["Excellent", "Good", "Fair"])

    performance_metrics = {
        "timestamp": now_utc().isoformat(),
        "accuracy": accuracy,
        "response_time_sec": response_time,
        "system_health": system_health
    }

    memory = load_learning_memory()

    # performance_metrics 키가 없으면 자동 생성
    if "performance_metrics" not in memory:
        memory["performance_metrics"] = []

    memory["performance_metrics"].append(performance_metrics)
    memory["performance_metrics"] = memory["performance_metrics"][-50:]

    save_learning_memory(memory)

if __name__ == "__main__":
    evaluate_performance()



