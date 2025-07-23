import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import json

def build_prompt():
    with open("memory_timeline.json", "r", encoding="utf-8") as f:
        timeline = json.load(f)

    prompt_lines = []
    for item in timeline:
        if item.get("type") in ["lock", "override", "default"]:
            line = f"[{item['timestamp']}] {item['content']}"
            prompt_lines.append(line)

    return "\n".join(prompt_lines)

if __name__ == "__main__":
    prompt = build_prompt()
    print("📤 복원 프롬프트:")
    print(prompt)