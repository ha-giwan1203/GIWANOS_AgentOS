import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)


import json
import os
from datetime import datetime

TIMELINE_PATH = "memory_timeline.json"

def load_timeline():
    if not os.path.exists(TIMELINE_PATH):
        return []
    with open(TIMELINE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_timeline(timeline):
    with open(TIMELINE_PATH, "w", encoding="utf-8") as f:
        json.dump(timeline, f, indent=2, ensure_ascii=False)

def add_memory(content, type="default", priority="normal"):
    timeline = load_timeline()
    new_item = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "content": content,
        "type": type,
        "priority": priority
    }
    timeline.append(new_item)
    timeline.sort(key=lambda x: x["timestamp"])
    save_timeline(timeline)
    print(f"✅ 새로운 기억 추가됨: {new_item['timestamp']} | {content} ({type}, {priority})")

# 예시 실행 (테스트용)
if __name__ == "__main__":
    add_memory("테스트 기억 추가됨", type="note", priority="low")
