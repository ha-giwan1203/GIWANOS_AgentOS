import sys
import io

# 윈도우 콘솔을 UTF-8로 재설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


import json
import os

TIMELINE_PATH = "memory_timeline.json"
RESTORE_PATH = "restore_prompt.txt"

def load_timeline():
    if not os.path.exists(TIMELINE_PATH):
        print("❌ memory_timeline.json 파일이 없습니다.")
        return []

    with open(TIMELINE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_restore_prompt(timeline):
    timeline_sorted = sorted(timeline, key=lambda x: x["timestamp"])
    prompt_lines = []
    for m in timeline_sorted:
        if m.get("type") in ["lock", "override", "default"]:
            prompt_lines.append(f"[{m['timestamp']}] {m['content']}")
    return "\n".join(prompt_lines)

def write_restore_prompt(prompt_text):
    with open(RESTORE_PATH, "w", encoding="utf-8") as f:
        f.write(prompt_text)
    print(f"✅ restore_prompt.txt에 복원 프롬프트 저장 완료")

if __name__ == "__main__":
    timeline = load_timeline()
    if timeline:
        prompt = generate_restore_prompt(timeline)
        write_restore_prompt(prompt)
