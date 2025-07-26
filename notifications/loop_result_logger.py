# loop_result_logger.py
import os
import json
import datetime

RESULT_LOG = "loop_result_log.json"

def save_loop_result(result: dict):
    os.makedirs(os.path.dirname(RESULT_LOG), exist_ok=True) if os.path.dirname(RESULT_LOG) else None
    if os.path.exists(RESULT_LOG):
        with open(RESULT_LOG, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "result": result
    }
    data.append(entry)

    with open(RESULT_LOG, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"📝 회고 결과 저장됨: {RESULT_LOG}")
