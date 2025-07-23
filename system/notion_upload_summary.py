
import os
import json
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def find_latest_weekly_summary():
    md_dir = Path("reflection_md")
    files = sorted(md_dir.glob("weekly_summary_*.md"), key=os.path.getmtime, reverse=True)
    return files[0] if files else None

def upload_weekly_summary(md_path, title="GIWANOS 주간 요약"):
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        print("❌ Notion 정보 누락")
        return

    if not md_path.exists():
        print("❌ 요약 파일이 없습니다:", md_path)
        return

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    created_date = datetime.now().isoformat()
    payload = {
        "parent": { "database_id": NOTION_DATABASE_ID },
        "properties": {
            "제목": { "title": [{ "text": { "content": md_path.stem }}]},
            "날짜": { "date": { "start": created_date }},
            "설명": { "rich_text": [{ "text": { "content": title }}]},
            "유형": { "select": { "name": "MD" }},
            "상태": { "status": { "name": "업로드 완료" }}
        },
        "children": [{
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": { "content": content[:1900] }
                }]
            }
        }]
    }

    res = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=payload)
    print("📤 Notion 응답 코드:", res.status_code)
    if res.status_code in [200, 201]:
        print("✅ Notion DB 업로드 성공")
    else:
        print("❌ 실패:", res.status_code, res.text)

def main():
    file = find_latest_weekly_summary()
    if not file:
        print("❌ 최신 요약 파일이 없습니다.")
        return
    upload_weekly_summary(file)

if __name__ == "__main__":
    main()
