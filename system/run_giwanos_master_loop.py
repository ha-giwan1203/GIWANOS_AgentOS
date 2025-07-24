
import subprocess
import os
from datetime import datetime

def run_command(command, cwd=None):
    result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True, encoding='utf-8')
    print(result.stdout)
    if result.stderr:
        print(f"에러 발생: {result.stderr}")

def main():
    base_path = "C:/giwanos"
    
    # Step 1: 주간 요약 생성
    print("🚀 주간 요약 생성 시작")
    run_command("python giwanos_agent/controller.py weekly_summary", cwd=base_path)
    
    # Step 2: Notion 자동 업로드
    print("📌 Notion 자동 업로드 시작")
    notion_path = os.path.join(base_path, "notion_integration")
    run_command("python upload_notion_result.py", cwd=notion_path)
    
    # Step 3: GitHub 최신 상태 자동 동기화
    print("☁️ GitHub 자동 동기화 시작")
    run_command("git add .", cwd=base_path)
    run_command(f'git commit -m "최종 통합 루프 자동 업데이트 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"', cwd=base_path)
    run_command("git push origin main", cwd=base_path)
    
    print("✅ 최종 통합 루프 모든 작업 완료!")

if __name__ == "__main__":
    main()
