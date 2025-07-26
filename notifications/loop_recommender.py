import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import json
from collections import Counter

def recommend_loop(history_file="loop_history.json"):
    if not os.path.exists(history_file):
        print("❌ 실행 기록이 없습니다.")
        return

    with open(history_file, "r", encoding="utf-8") as f:
        history = json.load(f)

    loops = [entry["loop"] for entry in history.values()]
    count = Counter(loops)
    most_common = count.most_common()

    print("📊 루프 실행 횟수:")
    for loop, freq in most_common:
        print(f" • {loop}: {freq}회")

    if most_common:
        last_loop = most_common[0][0]
        recommendation = {
            "loop_reflection": "upload_final_runner",
            "upload_final_runner": "loop_execution_summary",
            "loop_backup_logger": "loop_result_cleaner"
        }.get(last_loop, "loop_reflection")

        print(f"🧠 다음 추천 루프: {recommendation}")
    else:
        print("⚠️ 데이터가 부족합니다.")

if __name__ == "__main__":
    import os
    recommend_loop()
