import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import json

def clean_duplicates(timeline):
    seen = set()
    cleaned = []
    for item in timeline:
        key = item["content"].strip()
        if key not in seen:
            cleaned.append(item)
            seen.add(key)
    return cleaned

if __name__ == "__main__":
    with open("memory_timeline.json", "r", encoding="utf-8") as f:
        timeline = json.load(f)

    cleaned = clean_duplicates(timeline)

    with open("memory_cleaned.json", "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

    print(f"🧹 중복 제거 후 {len(cleaned)}개의 기억 항목 저장됨 (memory_cleaned.json)")