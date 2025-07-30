
import json
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)

MEMORY_PATH = "C:/giwanos/memory/learning_memory.json"
MAX_ENTRIES = 50

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
        logging.info("✅ 적응형 메모리 우선순위 저장 성공")
    except Exception as e:
        logging.error(f"적응형 메모리 저장 실패: {e}")

def prioritize_memory():
    memory = load_learning_memory()

    # 중요도 계산 예시: 항목 길이 기준 (실제 로직은 중요도나 사용 빈도 기준으로 변경 권장)
    memory["recent_events"] = sorted(memory["recent_events"], key=lambda x: len(x["event"]), reverse=True)[:MAX_ENTRIES]
    memory["insights"] = sorted(memory["insights"], key=lambda x: len(x["insight"]), reverse=True)[:MAX_ENTRIES]
    memory["performance_metrics"] = sorted(memory["performance_metrics"], key=lambda x: x["accuracy"], reverse=True)[:MAX_ENTRIES]

    save_learning_memory(memory)

if __name__ == "__main__":
    prioritize_memory()
