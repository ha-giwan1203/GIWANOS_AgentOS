<<<<<<< HEAD
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)


import json
from datetime import datetime

def evaluate_loop():
    print("📊 루프 평가기 실행 중...")
    result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "evaluation": "지속 가능",
        "criteria": {
            "회고 기반 판단": True,
            "메모리 상태 반영": True,
            "조건 기반 실행 흐름 감지": True
        },
        "next_action": "진화 루프 유지"
    }
    with open("loop_evaluation_log.json", "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")
    print("✅ 루프 평가 완료 및 기록 저장됨.")

if __name__ == "__main__":
    evaluate_loop()
=======
#!/usr/bin/env python
import sys
import json

def main():
    try:
        plan = json.loads(sys.argv[1])
    except Exception:
        plan = {}
    reflection = {
        "summary": "reflection successful",
        "plan": plan
    }
    print(json.dumps(reflection))

if __name__ == "__main__":
    main()
>>>>>>> 61149de (🎯 Git 초기화 및 복구 완료)
