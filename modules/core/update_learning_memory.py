"""
update_learning_memory.py

- 평가 결과를 기반으로 learning_memory.json을 자동 업데이트합니다.
- insights, performance_metrics를 누적 저장합니다.
"""

import json
import os
from datetime import datetime

LEARNING_MEMORY_PATH = "C:/giwanos/memory/learning_memory.json"
EVALUATION_LOG_PATH = "C:/giwanos/logs/evaluation_result.json"  # 평가 결과는 여기에 저장된다고 가정

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_insight(result):
    if "summary" in result:
        return result["summary"]
    elif "insight" in result:
        return result["insight"]
    return "N/A"

def update_learning_memory():
    memory = load_json(LEARNING_MEMORY_PATH)
    evaluation = load_json(EVALUATION_LOG_PATH)

    # 기본 구조 보장
    memory.setdefault("recent_events", [])
    memory.setdefault("insights", [])
    memory.setdefault("user_behavior", [])
    memory.setdefault("performance_metrics", [])

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    insight = extract_insight(evaluation)
    score = evaluation.get("score", -1)

    # 업데이트
    memory["insights"].append({
        "timestamp": timestamp,
        "insight": insight
    })

    memory["performance_metrics"].append({
        "timestamp": timestamp,
        "score": score
    })

    save_json(memory, LEARNING_MEMORY_PATH)
    print(f"[✅] learning_memory.json 업데이트 완료 at {timestamp}")

if __name__ == "__main__":
    update_learning_memory()
