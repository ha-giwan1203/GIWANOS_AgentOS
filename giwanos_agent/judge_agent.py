
class JudgeAgent:
    def __init__(self):
        print("[JudgeAgent] 🧠 초기화 완료")

    def run_plan_and_execute(self, user_prompt=""):
        print("[JudgeAgent] 🧠 플래너가 판단한 대로 루프 실행을 시작합니다.")
        plan_result = self.plan(user_prompt)
        execute_result = self.execute(plan_result)
        return execute_result

    def plan(self, user_prompt):
        print(f"[JudgeAgent] 📌 계획 수립: {user_prompt}")
        return "auto"

    def execute(self, plan_result):
        print(f"[JudgeAgent] 🚀 계획 '{plan_result}' 실행 중")
        return f"'{plan_result}' 실행 완료"
