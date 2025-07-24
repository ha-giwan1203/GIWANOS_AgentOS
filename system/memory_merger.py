import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import json
from datetime import datetime, timedelta
from difflib import SequenceMatcher

MERGE_WINDOW_MINUTES = 10
SIMILARITY_THRESHOLD = 0.85

def is_similar(a, b):
    return SequenceMatcher(None, a, b).ratio() >= SIMILARITY_THRESHOLD

def merge_timeline(timeline):
    merged = []
    skip = set()
    for i in range(len(timeline)):
        if i in skip:
            continue
        base = timeline[i]
        base_time = datetime.fromisoformat(base["timestamp"])
        group = [base["content"]]
        for j in range(i+1, len(timeline)):
            if j in skip:
                continue
            compare = timeline[j]
            compare_time = datetime.fromisoformat(compare["timestamp"])
            if abs((compare_time - base_time).total_seconds()) <= MERGE_WINDOW_MINUTES * 60:
                if is_similar(base["content"], compare["content"]):
                    group.append(compare["content"])
                    skip.add(j)
        if len(group) > 1:
            merged.append({
                "timestamp": base["timestamp"],
                "merged_content": " / ".join(group),
                "priority": base.get("priority", "normal")
            })
        else:
            merged.append(base)
    return merged

if __name__ == "__main__":
    with open("memory_timeline.json", "r", encoding="utf-8") as f:
        timeline = json.load(f)
    merged = merge_timeline(timeline)
    with open("memory_merged.json", "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    print("✅ memory_merged.json에 병합 결과 저장됨")