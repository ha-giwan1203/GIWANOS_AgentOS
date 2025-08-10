import os, requests, json

def get_notion_db_properties(token, database_id):
    url = f"https://api.notion.com/v1/databases/{database_id}"
    headers = {"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        props = r.json().get("properties", {})
        print("✅ 데이터베이스 속성 정보 감지 성공!")
        print(json.dumps(props, ensure_ascii=False, indent=2))
    else:
        print(f"❌ 속성 정보 가져오기 실패: {r.status_code} {r.text}")

def main():
    token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DATABASE_ID")
    get_notion_db_properties(token, database_id)
