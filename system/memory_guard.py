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

def detect_conflict(timeline, new_content, strict=True):
    for item in timeline:
        if item["content"].strip() == new_content.strip():
            print(f"⚠️ 동일한 선언 이미 존재: [{item['timestamp']}] {item['content']}")
            return True
        if strict and new_content.strip() in item["content"].strip():
            print(f"⚠️ 유사 선언 충돌 가능성 있음: [{item['timestamp']}] {item['content']}")
            return True
    return False

def add_protected_memory(content, type="default", priority="normal"):
    timeline = load_timeline()
    if detect_conflict(timeline, content):
        print("❌ 충돌 발생: 선언 추가가 차단되었습니다.")
        return

    new_item = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "content": content,
        "type": type,
        "priority": priority
    }
    timeline.append(new_item)
    timeline.sort(key=lambda x: x["timestamp"])

    with open(TIMELINE_PATH, "w", encoding="utf-8") as f:
        json.dump(timeline, f, indent=2, ensure_ascii=False)

    print(f"✅ 선언 추가 완료: {new_item['timestamp']} | {content} ({type}, {priority})")

if __name__ == "__main__":
    # 테스트 실행 예시
    add_protected_memory("GPT는 더 이상 진화 흐름을 제안하지 않는다", type="lock", priority="critical")
