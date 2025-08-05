"""
🚀 VELOS(벨로스) 시스템 운영 선언문

이 시스템은 GPT-4o Turbo 기반의 고도 사고형 운영 시스템 VELOS이다.
모든 회고는 실제 판단 흐름을 기억하고, 반복을 방지하며, 설명 가능한 시스템 행동을 위해 기록된다.
이 스크립트는 최근 메모리 기반 대화 흐름을 자동으로 요약하여 회고 파일로 저장한다.
"""

import os
import json
from datetime import datetime

MEMORY_PATH = "C:/giwanos/data/memory/learning_memory.json"
REFLECTION_DIR = "C:/giwanos/data/reflections"

def load_learning_memory(limit=10):
    try:
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data[-limit:] if isinstance(data, list) else []
    except:
        return []

def generate_summary(memory):
    if not memory:
        return "최근 대화 기록이 없어 회고를 생성할 수 없습니다.", "unknown"

    highlights = []
    level = "normal"

    for entry in memory:
        if "파일명 변경" in str(entry) or "기억 단절" in str(entry):
            highlights.append("🚨 동일 실수 반복 지적됨: " + entry.get("summary", ""))
            level = "critical"
        elif "검증 없이 파일 제공" in str(entry):
            highlights.append("⚠️ 검증 생략 문제: " + entry.get("summary", ""))
            if level != "critical":
                level = "warning"
        else:
            highlights.append("✅ " + entry.get("summary", ""))

    summary = "\n".join(highlights)
    return summary, level

def save_reflection(summary, level):
    os.makedirs(REFLECTION_DIR, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
    filename = f"reflection_memory_{timestamp}.json"
    path = os.path.join(REFLECTION_DIR, filename)

    data = {
        "timestamp": timestamp,
        "category": "memory_reflection",
        "summary": summary,
        "level": level
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return path

def run_memory_reflection():
    memory = load_learning_memory()
    summary, level = generate_summary(memory)
    return save_reflection(summary, level)

# 마스터 루프 호환성
generate_memory_reflection = run_memory_reflection
