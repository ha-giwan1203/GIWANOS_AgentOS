# VELOS 기억 기반 판단 시스템 - memory_reader.py
# 저장된 learning_memory.json 및 reflection_memory_*.json에서 최근 명령과 회고 요약을 추출해 context로 반환합니다.

import json
import os
from pathlib import Path
from datetime import datetime

def read_memory_context(
    memory_path="C:/giwanos/data/memory/learning_memory.json",
    reflection_dir="C:/giwanos/data/reflections/",
    max_count=5
):
    context_parts = []

    # 🔹 1. 사용자 명령 요약 추출
    try:
        with open(memory_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            insights = data.get("insights", [])
            user_cmds = [i["insight"] for i in insights if i.get("from") == "user"][-max_count:]
            if user_cmds:
                context_parts.append("📌 과거 사용자 명령:")
                for cmd in user_cmds:
                    context_parts.append(f"- {cmd}")
    except Exception as e:
        context_parts.append(f"⚠️ 사용자 메모리 읽기 실패: {e}")

    # 🔹 2. 최근 회고 요약 추출
    try:
        reflection_files = sorted(
            [f for f in os.listdir(reflection_dir) if f.startswith("reflection_memory") and f.endswith(".json")],
            reverse=True
        )[:max_count]

        reflections = []
        for fname in reflection_files:
            with open(Path(reflection_dir) / fname, "r", encoding="utf-8") as f:
                reflection = json.load(f)
                summary = reflection.get("summary")
                if summary:
                    reflections.append(f"- {summary}")

        if reflections:
            context_parts.append("\n🧠 최근 시스템 회고:")
            context_parts.extend(reflections)
    except Exception as e:
        context_parts.append(f"⚠️ 회고 로딩 실패: {e}")

    # 🧠 최종 context 반환
    return "\n".join(context_parts) if context_parts else "과거 기억 없음"


