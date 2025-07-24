
# judge_agent.py
import os
from datetime import datetime

class JudgeAgent:
    def __init__(self):
        self.initialized = False

    def initialize(self):
        # 초기화 로직
        print("[JudgeAgent] 🧠 초기화 완료")
        self.initialized = True

    def run(self, mode="auto"):
        # 주어진 모드에 따라 적절한 루프 실행
        if not self.initialized:
            self.initialize()

        if mode == "weekly_summary":
            return self.run_loop("weekly_summary")
        elif mode == "auto":
            return self.auto_run()
        else:
            print(f"[JudgeAgent] ⚠️ '{mode}' 모드를 찾을 수 없습니다.")
            return None

    def auto_run(self):
        # 자동 플래너 기반 실행 로직
        print("[JudgeAgent] 🤖 자동 플래너 기반 실행 시작")
        return self.run_plan_and_execute("auto")

    def run_loop(self, loop_name):
        print(f"[JudgeAgent] 🚀 '{loop_name}' 루프 실행 시작")
        if loop_name == "weekly_summary":
            return self.generate_weekly_summary()
        else:
            print(f"[JudgeAgent] ⚠️ '{loop_name}' 루프 정의가 없습니다.")
            return False

    def generate_weekly_summary(self):
        summary_dir = "C:/giwanos/summaries"
        os.makedirs(summary_dir, exist_ok=True)

        # 요약 파일 이름을 표준 형식으로 생성
        week_number = datetime.now().isocalendar().week
        year = datetime.now().year
        summary_file = os.path.join(summary_dir, f"weekly_summary_{year}W{week_number}.md")

        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(f"# Weekly Summary {year}W{week_number}\n\n")
            f.write("- 주간 요약 자동 생성 완료\n")
            f.write(f"- 생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        print(f"[JudgeAgent] ✅ 주간 요약 파일 생성 완료 → {summary_file}")
        return True

    def run_plan_and_execute(self, user_prompt):
        # 플래너 기반으로 판단된 루프 실행
        print(f"[JudgeAgent] 📌 플래너 기반 계획 수립 및 실행: {user_prompt}")
        
        if user_prompt == "auto":
            # auto 모드에서 실행할 루프 정의
            loops_to_run = ["weekly_summary"]
        else:
            loops_to_run = [user_prompt]

        for loop in loops_to_run:
            self.run_loop(loop)

        print(f"[JudgeAgent] 🤖 '{user_prompt}' 실행 완료")
        return True
