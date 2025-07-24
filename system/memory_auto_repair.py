import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import json
from difflib import SequenceMatcher

def is_similar(a, b):
    return SequenceMatcher(None, a, b).ratio() >= 0.9

def auto_merge_similar(timeline):
    merged = []
    seen = set()

    for i, base in enumerate(timeline):
        if i in seen:
            continue
        group = [base]
        for j in range(i+1, len(timeline)):
            if j in seen:
                continue
            if is_similar(base["content"], timeline[j]["content"]):
                group.append(timeline[j])
                seen.add(j)
        if len(group) > 1:
            base["content"] += "  ⛓ (병합됨)"
        merged.append(base)
    return merged

if __name__ == "__main__":
    with open("memory_timeline.json", "r", encoding="utf-8") as f:
        timeline = json.load(f)
    repaired = auto_merge_similar(timeline)
    with open("memory_repaired.json", "w", encoding="utf-8") as f:
        json.dump(repaired, f, indent=2, ensure_ascii=False)
    print("✅ memory_repaired.json 파일로 유사 선언 병합 저장 완료")