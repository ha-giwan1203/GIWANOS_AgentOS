# VELOS 기억 기반 판단 시스템 - memory_reader.py (하드코딩 제거)
from __future__ import annotations

import json
from pathlib import Path
from modules.core.config import LEARNING_MEMORY, REFLECTION_DIR


def read_memory_context(
    memory_path: str | Path = LEARNING_MEMORY,
    reflection_dir: str | Path = REFLECTION_DIR,
    max_count: int = 5
) -> str:
    context_parts = []

    # 1) 사용자 명령 요약
    try:
        mp = Path(memory_path)
        if mp.exists():
            data = json.loads(mp.read_text(encoding="utf-8"))
            insights = data.get("insights", [])
            user_cmds = [i.get("insight") for i in insights if i.get("from") == "user"][-max_count:]
            if user_cmds:
                context_parts.append("📌 과거 사용자 명령:")
                context_parts.extend(f"- {cmd}" for cmd in user_cmds if cmd)
    except Exception as e:
        context_parts.append(f"⚠️ 사용자 메모리 읽기 실패: {e}")

    # 2) 최근 회고 요약
    try:
        rf = Path(reflection_dir)
        if rf.exists():
            files = sorted([p for p in rf.glob("reflection_memory*.json")], reverse=True)[:max_count]
            reflections = []
            for p in files:
                js = json.loads(p.read_text(encoding="utf-8"))
                s = js.get("summary")
                if s:
                    reflections.append(f"- {s}")
            if reflections:
                context_parts.append("\n🧠 최근 시스템 회고:")
                context_parts.extend(reflections)
    except Exception as e:
        context_parts.append(f"⚠️ 회고 로딩 실패: {e}")

    return "\n".join(context_parts) if context_parts else "과거 기억 없음"
