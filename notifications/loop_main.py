import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import subprocess

def run_judgement():
    print("🧠 루프 판단 실행 중...")
    subprocess.run(["python", "loop_modules/judge_agent.py"])

def run_reflection():
    print("📝 회고 루프 실행 중...")
    subprocess.run(["python", "loop_modules/loop_reflection_gpt_agent.py"])

def run_leaderboard():
    print("📊 리더보드 생성 중...")
    subprocess.run(["python", "loop_modules/loop_leaderboard_report.py"])

def run_dashboard():
    print("📈 대시보드 실행 중...")
    subprocess.run(["streamlit", "run", "loop_modules/loop_dashboard_streamlit.py"])

def run_chain():
    print("🔁 체인 실행 준비 중...")
    subprocess.run(["python", "loop_modules/loop_chain_runner.py"])

if __name__ == "__main__":
    print("""
========== GIWANOS 루프 메인 실행기 ==========
1. 루프 판단 실행
2. 회고 루프 실행
3. 리더보드 보고서 생성
4. Streamlit 대시보드 실행
5. 루프 체인 실행
0. 종료
==============================================
""")
    choice = input("실행할 작업을 선택하세요 (번호 입력): ")
    if choice == "1":
        run_judgement()
    elif choice == "2":
        run_reflection()
    elif choice == "3":
        run_leaderboard()
    elif choice == "4":
        run_dashboard()
    elif choice == "5":
        run_chain()
    else:
        print("✅ 종료됨.")
