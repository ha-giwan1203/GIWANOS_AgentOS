import sys
import io
from dotenv import load_dotenv
import os
import requests
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

try:
    # Ensure UTF-8 output in Windows console
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

def upload_to_notion(file_path, page_title="GIWANOS 전송 결과"):
    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
    NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        print("❌ 환경변수에서 NOTION 정보가 누락되었습니다.")
        return

    if not os.path.exists(file_path):
        print(f"❌ 업로드할 파일이 존재하지 않습니다: {file_path}")
        return

    filename = os.path.basename(file_path)
    ext = filename.split(".")[-1].upper()
    created_date = datetime.now().isoformat()

    payload = {
        "parent": { "database_id": NOTION_DATABASE_ID },
        "properties": {
            "제목": { "title": [{ "text": { "content": filename }}]},
            "날짜": { "date": { "start": created_date }},
            "설명": { "rich_text": [{ "text": { "content": page_title }}]},
            "경로": { "rich_text": [{ "text": { "content": file_path }}]},
            "유형": { "select": { "name": ext }},
            "상태": { "status": { "name": "업로드 완료" }}
        }
    }

    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    response = requests.post("https://api.notion.com/v1/pages", headers=headers, json=payload)

    print("📤 Notion 응답 코드:", response.status_code)
    if response.status_code == 200:
        print("✅ Notion 카드 생성 완료")
    else:
        print("❌ Notion 업로드 실패:", response.text)

# ✅ report_agent가 호출할 수 있게 래퍼 추가
def send_to_notion(file_path):
    upload_to_notion(file_path)
