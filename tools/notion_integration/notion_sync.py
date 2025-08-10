import os
from modules.core.time_utils import now_utc, now_kst, iso_utc, monotonic
from notion_client import Client
from datetime import datetime

def get_database_properties(notion, database_id):
    return notion.databases.retrieve(database_id=database_id)["properties"]

def main():
    notion_token = os.getenv('NOTION_TOKEN')
    database_id = os.getenv('NOTION_DATABASE_ID')
    notion = Client(auth=notion_token)

    props = get_database_properties(notion, database_id)
    new_page_props = {}
    for name, info in props.items():
        t = info["type"]
        if t == "title":
            new_page_props[name] = {"title": [{"text": {"content": "GIWANOS Test Entry"}}]}
        elif t == "date":
            new_page_props[name] = {"date": {"start": now_kst().strftime("%Y-%m-%d")}}
        elif t == "status" and info["status"]["options"]:
            new_page_props[name] = {"status": {"name": info["status"]["options"][0]["name"]}}

    notion.pages.create(parent={"database_id": database_id}, properties=new_page_props)
    print("[✅ Notion 데이터베이스 동기화 성공]")

