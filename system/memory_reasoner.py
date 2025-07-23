import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import json
from difflib import SequenceMatcher

def reason_relations(timeline):
    reasons = []
    for i in range(1, len(timeline)):
        a = timeline[i-1]
        b = timeline[i]
        sim = SequenceMatcher(None, a["content"], b["content"]).ratio()
        if sim < 0.5:
            reasons.append({
                "from": a["content"],
                "to": b["content"],
                "reason": "새로운 주제로 전환됨"
            })
        else:
            reasons.append({
                "from": a["content"],
                "to": b["content"],
                "reason": "내용이 연결됨 (유사)"
            })
    return reasons

if __name__ == "__main__":
    with open("memory_timeline.json", "r", encoding="utf-8") as f:
        timeline = json.load(f)
    relations = reason_relations(timeline)
    for r in relations:
        print(f"🔄 {r['from']} → {r['to']}  ({r['reason']})")