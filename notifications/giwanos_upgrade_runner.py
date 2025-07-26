
import os
import subprocess

print("🚀 GIWANOS 고도화 루프 실행 시작")

# Step 1: 회고 피드백 루프 실행
print("\n▶️ rag_feedback_loop.py 실행 중...")
subprocess.run(["python", "advanced_modules/rag_feedback_loop.py"], check=True)

# Step 2: 재랭킹 테스트 실행
print("\n▶️ test_re_ranker.py 실행 중...")
subprocess.run(["python", "advanced_modules/test_re_ranker.py"], check=True)

# Step 3: CoT 평가 템플릿 실행
print("\n▶️ test_cot_prompt.py 실행 중...")
subprocess.run(["python", "advanced_modules/test_cot_prompt.py"], check=True)

print("\n✅ 모든 고도화 루프 실행 완료")
