
import requests
import json

def load_config():
    with open("notion_config.json", "r", encoding="utf-8") as file:
        return json.load(file)

def get_notion_db_properties(token, database_id):
    url = f"https://api.notion.com/v1/databases/{database_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        db_info = response.json()
        properties = db_info.get("properties", {})
        print("✅ 데이터베이스 속성 정보 감지 성공!")
        print(json.dumps(properties, ensure_ascii=False, indent=4))
    else:
        print(f"❌ 속성 정보 가져오기 실패: {response.text}")

def main():
    config = load_config()
    get_notion_db_properties(config['token'], config['database_id'])

if __name__ == "__main__":
    main()
