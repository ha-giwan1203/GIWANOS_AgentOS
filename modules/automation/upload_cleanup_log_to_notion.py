
from modules.core.time_utils import now_utc, now_kst, iso_utc, monotonic
"""
VELOS 삭제 로그 Notion 업로드 스크립트

- 대상: C:/giwanos/data/logs/report_cleanup_log.json
- 업로드: 지정된 Notion 데이터베이스에 삭제 로그 요약 전송
"""

import json
import os
from datetime import datetime
from notion_client import Client

# 설정
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_LOG_DATABASE_ID")
LOG_PATH = "C:/giwanos/data/logs/report_cleanup_log.json"

notion = Client(auth=NOTION_TOKEN)

def summarize_deleted(logs):
    folders = {}
    for item in logs:
        folder = item["folder"]
        folders[folder] = folders.get(folder, 0) + 1
    return folders

def upload_cleanup_log_to_notion():
    if not os.path.exists(LOG_PATH):
        print("❌ 삭제 로그 파일이 존재하지 않습니다.")
        return

    with open(LOG_PATH, "r", encoding="utf-8") as f:
        try:
            logs = json.load(f)
        except:
            print("❌ 로그 JSON 파싱 실패")
            return

    # 오늘 삭제된 항목만 필터
    today_str = now_kst().strftime("%Y-%m-%d")
    today_logs = [l for l in logs if l["deleted_at"].startswith(today_str)]

    if not today_logs:
        print("✅ 오늘 삭제된 항목이 없습니다. 업로드 생략.")
        return

    summary = summarize_deleted(today_logs)
    summary_text = "\n".join([f"{os.path.basename(k)}: {v}개" for k, v in summary.items()])

    page = {
        "parent": { "database_id": NOTION_DATABASE_ID },
        "properties": {
            "제목": { "title": [{ "text": { "content": f"VELOS 삭제 로그 - {today_str}" } }] },
            "삭제 요약": { "rich_text": [{ "text": { "content": summary_text } }] },
            "삭제 수": { "number": len(today_logs) },
            "업로드 시간": { "date": { "start": now_utc().isoformat() } }
        }
    }

    notion.pages.create(**page)
    print("✅ Notion 업로드 완료")

if __name__ == "__main__":
    upload_cleanup_log_to_notion()



