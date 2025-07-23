import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)


import os
import requests

token = os.getenv("NOTION_TOKEN")
database_id = os.getenv("NOTION_DATABASE_ID")

if not token or not database_id:
    print("❌ Notion 연동 정보 없음")
else:
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    data = {
        "parent": {"database_id": database_id},
        "properties": {
            "제목": {"title": [{"text": {"content": "✅ GIWANOS Notion 테스트"}}]}
        }
    }
    res = requests.post(url, headers=headers, json=data)
    if res.status_code == 200 or res.status_code == 201:
        print("✅ Notion 업로드 성공")
    else:
        print(f"❌ Notion 전송 실패: {res.status_code}")
