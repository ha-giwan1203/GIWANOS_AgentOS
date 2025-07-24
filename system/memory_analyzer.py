import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import json
from datetime import datetime

def analyze_timeline():
    with open("memory_timeline.json", "r", encoding="utf-8") as f:
        timeline = json.load(f)

    timeline_sorted = sorted(timeline, key=lambda x: x["timestamp"])
    print("📊 기억 흐름 분석:")
    for i, item in enumerate(timeline_sorted):
        ts = item["timestamp"]
        summary = f"[{ts}] {item['content']} ({item['type']}, {item['priority']})"
        print(f"{i+1:02d}. {summary}")

if __name__ == "__main__":
    analyze_timeline()