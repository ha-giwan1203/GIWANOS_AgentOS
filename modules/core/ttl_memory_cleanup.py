
import json
import os
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)

MEMORY_PATH = "C:/giwanos/memory/learning_memory.json"
TTL_DAYS = 30  # 데이터 유지 기간 설정 (30일)

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
        logging.info("✅ 학습 메모리 저장 성공 (TTL 정리 완료)")
    except Exception as e:
        logging.error(f"학습 메모리 저장 실패: {e}")

def ttl_cleanup():
    memory = load_learning_memory()
    cutoff_date = datetime.now() - timedelta(days=TTL_DAYS)

    def filter_old_entries(entries):
        return [entry for entry in entries if datetime.fromisoformat(entry["timestamp"]) > cutoff_date]

    memory["recent_events"] = filter_old_entries(memory["recent_events"])
    memory["insights"] = filter_old_entries(memory["insights"])

    save_learning_memory(memory)

if __name__ == "__main__":
    ttl_cleanup()
