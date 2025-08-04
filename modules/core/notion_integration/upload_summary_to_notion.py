
import os
import datetime
import requests
from dotenv import load_dotenv

load_dotenv("C:/giwanos/configs/.env")

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")
REPORT_DIR = "C:/giwanos/data/reports"

def upload_summary_to_notion():
    today = datetime.datetime.now().strftime("%Y%m%d")
    summary_file = os.path.join(REPORT_DIR, f"weekly_summary_{today}.txt")

    if not os.path.exists(summary_file):
        print("❌ 요약 파일이 존재하지 않습니다:", summary_file)
        return

    with open(summary_file, "r", encoding="utf-8") as f:
        summary_text = f.read()

    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    url = f"https://api.notion.com/v1/blocks/{NOTION_PAGE_ID}/children"

    payload = {
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": summary_text[:2000]  # 블록 제한
                            }
                        }
                    ]
                }
            }
        ]
    }

    response = requests.patch(url, headers=headers, json=payload)
    if response.status_code == 200:
        print("✅ Notion 페이지에 요약 업로드 완료")
    else:
        print(f"❌ Notion 업로드 실패: {response.status_code} {response.text}")

if __name__ == "__main__":
    upload_summary_to_notion()
