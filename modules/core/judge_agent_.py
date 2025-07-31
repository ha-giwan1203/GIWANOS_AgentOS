
import json
import os

class JudgeAgent:
    def evaluate_files(self, file_info, days_unused):
        results = []
        for file in file_info:
            path, unused_days = file  # 실제 데이터 형식(튜플)에 맞게 수정
            action = "keep"
            if unused_days >= days_unused:
                action = "backup"
            results.append({"file": path, "action": action})

        os.makedirs("C:/giwanos/logs", exist_ok=True)
        with open("C:/giwanos/logs/evaluation_result.json", "w") as f:
            json.dump(results, f)

        return results
