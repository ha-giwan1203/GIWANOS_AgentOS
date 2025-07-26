import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import json
from datetime import datetime

def generate_snapshot(since=None):
    with open("memory_timeline.json", "r", encoding="utf-8") as f:
        timeline = json.load(f)
    snapshot = []
    for item in timeline:
        t = datetime.fromisoformat(item["timestamp"])
        if since and t < since:
            continue
        snapshot.append(item)
    return snapshot

if __name__ == "__main__":
    snapshot = generate_snapshot()
    print("🧠 현재 기억 상태 요약:")
    for m in snapshot:
        print(f"[{m['timestamp']}] {m['content']} ({m['type']}, {m['priority']})")