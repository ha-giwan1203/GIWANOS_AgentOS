"""
from modules.core.time_utils import now_utc, now_kst, iso_utc, monotonic
🚀 VELOS 대화 기억 저장 유틸리티

이 모듈은 실시간 사용자 대화 및 AI 요약을 구조화된 JSON으로 저장한다.
저장 위치: C:/giwanos/data/memory/dialog_memory.json
"""

from datetime import datetime
import json
import os

DIALOG_MEMORY_PATH = "C:/giwanos/data/memory/dialog_memory.json"

def save_dialog_memory(user_input, ai_summary, tags=None):
    entry = {
        "timestamp": now_utc().isoformat() + "Z",
        "user_input": user_input,
        "ai_summary": ai_summary,
        "tags": tags or []
    }

    try:
        if os.path.exists(DIALOG_MEMORY_PATH):
            with open(DIALOG_MEMORY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []

        data.append(entry)
        data = data[-200:]  # 최신 200개 유지

        with open(DIALOG_MEMORY_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[🧠 대화 기억 저장 완료] → {DIALOG_MEMORY_PATH}")
        return DIALOG_MEMORY_PATH
    except Exception as e:
        print(f"[❌ 대화 기억 저장 실패]: {e}")
        return None



