import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)


import json
from difflib import SequenceMatcher

THRESHOLD = 0.8  # 유사도 임계값

def load_timeline():
    with open("memory_timeline.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_compressed(compressed, path="memory_compressed.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(compressed, f, indent=2, ensure_ascii=False)

def is_similar(a, b):
    return SequenceMatcher(None, a, b).ratio() >= THRESHOLD

def compress_timeline(timeline):
    compressed = []
    used = set()

    for i, base in enumerate(timeline):
        if i in used:
            continue
        group = [base]
        for j in range(i+1, len(timeline)):
            if j in used:
                continue
            if is_similar(base["content"], timeline[j]["content"]):
                group.append(timeline[j])
                used.add(j)
        if len(group) > 1:
            compressed.append({
                "summary": base["content"],
                "grouped": group
            })
        else:
            compressed.append(base)
    return compressed

if __name__ == "__main__":
    timeline = load_timeline()
    result = compress_timeline(timeline)
    save_compressed(result)
    print(f"✅ {len(result)}개의 압축 결과 저장됨 (memory_compressed.json)")
