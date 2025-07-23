import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)


import os
import requests
import json

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}"
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28"
}

response = requests.get(url, headers=headers)
print("🔗 응답 코드:", response.status_code)

if response.status_code == 200:
    data = response.json()
    print("\n🧩 Notion Database Properties:")
    for name, prop in data["properties"].items():
        print(f"📌 {name}: {prop['type']}")
else:
    print("❌ 오류 발생:", response.text)
