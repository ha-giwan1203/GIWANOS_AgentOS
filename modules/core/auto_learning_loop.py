
import json
import os
import logging
from datetime import datetime

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
        logging.info("✅ 학습 메모리 저장 성공")
    except Exception as e:
        logging.error(f"학습 메모리 저장 실패: {e}")

def auto_update_learning_memory(event, insight):
    memory = load_learning_memory()
    timestamp = datetime.now().isoformat()

    # 이벤트 및 인사이트 추가
    memory["recent_events"].append({"timestamp": timestamp, "event": event})
    memory["insights"].append({"timestamp": timestamp, "insight": insight})

    # 최대 저장 개수 제한 (최근 50개만 유지)
    memory["recent_events"] = memory["recent_events"][-50:]
    memory["insights"] = memory["insights"][-50:]

    save_learning_memory(memory)

# 자동 학습 루틴 예시 (실제 사용 시 평가 로직에서 호출)
if __name__ == "__main__":
    example_event = "자동 학습 루틴 실행됨"
    example_insight = "학습 루틴이 정상적으로 동작하여 메모리를 업데이트했습니다."
    auto_update_learning_memory(example_event, example_insight)
