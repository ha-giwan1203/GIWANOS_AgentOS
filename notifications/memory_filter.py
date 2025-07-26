import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import json
from datetime import datetime, timedelta

def filter_recent(limit=3):
    with open("memory_timeline.json", "r", encoding="utf-8") as f:
        timeline = json.load(f)
    sorted_items = sorted(timeline, key=lambda x: x["timestamp"], reverse=True)
    return sorted_items[:limit]

def filter_since(hours=24):
    threshold = datetime.now() - timedelta(hours=hours)
    with open("memory_timeline.json", "r", encoding="utf-8") as f:
        timeline = json.load(f)
    return [item for item in timeline if datetime.fromisoformat(item["timestamp"]) >= threshold]

if __name__ == "__main__":
    print("🧩 최근 3개 선언:")
    for m in filter_recent():
        print(f"- {m['content']}")

    print("\n⏱️ 최근 24시간 내 선언:")
    for m in filter_since():
        print(f"- {m['content']}")