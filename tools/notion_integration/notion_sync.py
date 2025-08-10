import os
from notion_client import Client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv('C:/giwanos/config/.env')

def get_database_properties(notion, database_id):
    database = notion.databases.retrieve(database_id=database_id)
    return database["properties"]

def main():
    notion_token = os.getenv('NOTION_TOKEN')
    database_id = os.getenv('NOTION_DATABASE_ID')

    notion = Client(auth=notion_token)

    # 속성 자동 감지
    properties = get_database_properties(notion, database_id)

    # 속성 타입별 자동 매핑
    new_page_props = {}
    for prop_name, prop_info in properties.items():
        if prop_info["type"] == "title":
            new_page_props[prop_name] = {"title": [{"text": {"content": "GIWANOS Test Entry"}}]}
        elif prop_info["type"] == "date":
            new_page_props[prop_name] = {"date": {"start": datetime.now().strftime("%Y-%m-%d")}}
        elif prop_info["type"] == "status":
            status_options = prop_info["status"]["options"]
            if status_options:
                new_page_props[prop_name] = {"status": {"name": status_options[0]["name"]}}

    # Notion 페이지 생성
    notion.pages.create(parent={"database_id": database_id}, properties=new_page_props)
    print("[✅ Notion 데이터베이스 동기화 성공]")

if __name__ == "__main__":
    main()

