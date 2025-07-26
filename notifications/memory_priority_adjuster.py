import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import json
from datetime import datetime, timedelta

def adjust_priorities(timeline):
    now = datetime.now()
    for item in timeline:
        ts = datetime.fromisoformat(item["timestamp"])
        delta = (now - ts).days
        if delta > 60:
            item["priority"] = "low"
        elif delta > 30:
            item["priority"] = "normal"
        else:
            item["priority"] = "high"
    return timeline

if __name__ == "__main__":
    with open("memory_timeline.json", "r", encoding="utf-8") as f:
        timeline = json.load(f)

    adjusted = adjust_priorities(timeline)

    with open("memory_priority_adjusted.json", "w", encoding="utf-8") as f:
        json.dump(adjusted, f, indent=2, ensure_ascii=False)

    print("🔁 선언 우선순위 자동 조정 완료 (파일: memory_priority_adjusted.json)")