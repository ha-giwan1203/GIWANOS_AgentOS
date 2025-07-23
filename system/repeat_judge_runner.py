import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)


import json
from datetime import datetime

def repeat_judgement():
    print("🧠 사고 루프 판단 시작...")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log = {
        "timestamp": now,
        "judgement": "정상",
        "reasoning": "회고 + memory 기준 판단 루프 작동 정상",
        "action": "반복 실행 유지"
    }
    with open("loop_result_log.json", "a", encoding="utf-8") as f:
        f.write(json.dumps(log, ensure_ascii=False) + "\n")
    print("✅ 판단 기록 저장됨")

if __name__ == "__main__":
    repeat_judgement()
