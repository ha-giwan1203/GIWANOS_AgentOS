"""
judge_agent.py (자기 튜닝 루프 포함 버전)

- 평가 점수를 바탕으로 루프 순서를 자동 조정하는 기능 포함
"""

import json
from datetime import datetime

EVALUATION_RESULT_PATH = "C:/giwanos/logs/evaluation_result.json"

class JudgeAgent:
    def __init__(self):
        self.evaluation_score = self.load_evaluation_score()

    def load_evaluation_score(self):
        try:
            with open(EVALUATION_RESULT_PATH, "r", encoding="utf-8") as f:
                result = json.load(f)
                return result.get("score", 100)
        except Exception as e:
            print(f"[경고] 평가 결과 불러오기 실패: {e}")
            return 100

    def plan(self):
        print(f"[🧠] 현재 평가 점수: {self.evaluation_score}")
        if self.evaluation_score < 60:
            print("[⚠️] 낮은 점수 감지 → CoT 우선 루프 재실행 예정")
            return ["run_rag_feedback_loop", "run_cot_evaluation_loop", "run_reranker_loop"]
        elif self.evaluation_score < 80:
            print("[🔁] 평균 이하 성능 → CoT + Rerank 반복")
            return ["run_cot_evaluation_loop", "run_reranker_loop"]
        else:
            print("[✅] 양호한 성능 → 정상 루프 실행")
            return ["run_reflection_loop", "run_notion_upload", "run_git_sync"]

    def run_loop(self):
        plan = self.plan()
        for task in plan:
            print(f"→ 실행 예정: {task}")
            # 실제 함수는 루프에 연결되어 있어야 함
