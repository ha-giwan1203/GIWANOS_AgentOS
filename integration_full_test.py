
import subprocess
import logging
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv("C:/giwanos/config/.env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

logging.basicConfig(level=logging.ERROR, filename="C:/giwanos/data/logs/integration_full_test.log", format='%(asctime)s %(levelname)s %(message)s')

def run_script(script, description):
    try:
        subprocess.run(["python", script], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[✅ 성공] {description}")
    except subprocess.CalledProcessError as e:
        print(f"[❌ 실패] {description}: {e}")
        logging.error(f"{description}: {e}")

def test_gpt_api():
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "GIWANOS 시스템 테스트입니다."},
                {"role": "user", "content": "GPT 연동 테스트 메시지입니다."}
            ]
        )
        reply = response.choices[0].message.content.strip()
        print(f"[✅ 성공] GPT API 응답: {reply}")
    except Exception as e:
        print(f"[❌ 실패] GPT API 연동 오류: {e}")
        logging.error(f"GPT API 연동 오류: {e}")

def main():
    print("==========================================")
    print("🚀 GIWANOS 전체 연동 상태 통합 테스트 시작 🚀")
    print("==========================================\n")
    
    run_script("C:/giwanos/notion_integration/upload_notion_result.py", "Notion 연동 테스트")
    run_script("C:/giwanos/automation/git_management/git_sync.py", "GitHub 동기화 테스트")
    run_script("C:/giwanos/evaluation/human_readable_reports/generate_pdf_report.py", "이메일 보고서 발송 테스트")
    run_script("C:/giwanos/notifications/send_mobile_notification.py", "모바일 알림 전송 테스트")
    test_gpt_api()
    
    print("\n==========================================")
    print("✨ GIWANOS 전체 연동 상태 통합 테스트 완료 ✨")
    print("==========================================")

if __name__ == "__main__":
    main()
