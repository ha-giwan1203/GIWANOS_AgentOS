
import json
import os

class JudgeAgent:
    def evaluate_files(self, file_info, days_unused):
        results = []
        for file in file_info:
            path, unused_days = file  # 튜플 형태로 데이터를 정확히 받도록 수정함
            action = "keep"
            if unused_days >= days_unused:
                action = "backup"
            results.append({"file": path, "action": action})

        os.makedirs("C:/giwanos/logs", exist_ok=True)
        with open("C:/giwanos/logs/evaluation_result.json", "w") as f:
            json.dump(results, f)

        return results


