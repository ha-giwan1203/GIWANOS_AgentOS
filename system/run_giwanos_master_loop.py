import subprocess
import os

# index.lock 충돌 방지용 제거 루틴
lock_path = os.path.join('.git', 'index.lock')
if os.path.exists(lock_path):
    try:
        os.remove(lock_path)
        print('[🧹] index.lock 제거 완료')
    except Exception as e:
        print(f'[⚠️] index.lock 제거 실패: {e}')

print("🧠 JudgeAgent 플랜 실행 (plan-only)")
subprocess.run(["python", "giwanos_agent/judge_agent.py"], check=True)

print("🔁 회고 평가 루프 실행")
subprocess.run(["python", "advanced_modules/rag_feedback_loop.py"], check=True)

print("🔁 CoT 생성기 실행")
subprocess.run(["python", "advanced_modules/test_cot_prompt.py"], check=True)

print("🔁 재랭킹 평가기 실행")
subprocess.run(["python", "advanced_modules/test_re_ranker.py"], check=True)

print("📊 평가 통합")
subprocess.run(["python", "aggregate_evaluation_logs.py"], check=True)

print("🖨️ 회고 PDF 생성")
subprocess.run(["python", "generate_reflection_pdf.py"], check=True)

print("📄 PDF + 이메일 전송")
subprocess.run(["python", "send_evaluation_report.py"], check=True)

print("📤 회고 마크다운 Notion 전송")
notion_script = os.path.abspath(os.path.join("giwanos", "reporting", "upload_final_runner.py"))
subprocess.run(["python", notion_script], check=True)

print("☁️ GitHub 백업 동기화")
try:
    subprocess.run(["python", "git_sync_with_cleanup.py"], check=True)
    print("[✅] GitHub 백업 성공")
except Exception as e:
    print(f"[❌] GitHub 백업 실패 → 루프는 계속됨\n이유: {e}")

print("🗓️ 주간 요약 생성")
subprocess.run(["python", "weekly_summary_generator.py"], check=True)

print("📈 Streamlit 대시보드 갱신 (옵션)")
try:
    subprocess.run(["python", "status_dashboard.py"], check=True)
except Exception as e:
    print(f"[경고] 대시보드 실행 실패: {e}")
