# modules/core/notion_integration.py
import os
from dotenv import load_dotenv
from notion_client import Client
from datetime import datetime
import requests

load_dotenv('C:/giwanos/config/.env')

NOTION_TOKEN = os.getenv('NOTION_TOKEN')
DATABASE_ID = os.getenv('NOTION_DATABASE_ID')
PAGE_ID = os.getenv('NOTION_PAGE_ID')

notion = Client(auth=NOTION_TOKEN)

def add_notion_database_entry(title, status, description, entry_type="결과"):
    properties = {
        "제목": {"title": [{"text": {"content": title}}]},
        "상태": {"status": {"name": status}},
        "설명": {"rich_text": [{"text": {"content": description}}]},
        "유형": {"select": {"name": entry_type}},
        "날짜": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}}
    }

    notion.pages.create(parent={"database_id": DATABASE_ID}, properties=properties)


def upload_reflection_to_notion(reflection_text):
    properties = {
        "제목": {"title": [{"text": {"content": f"회고 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}}]},
        "상태": {"status": {"name": "회고"}},
        "설명": {"rich_text": [{"text": {"content": reflection_text}}]},
        "유형": {"select": {"name": "회고"}},
        "날짜": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}}
    }

    notion.pages.create(parent={"database_id": DATABASE_ID}, properties=properties)


def append_summary_block_to_page(summary_text):
    url = f"https://api.notion.com/v1/blocks/{PAGE_ID}/children"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    payload = {
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": summary_text}}]}
            }
        ]
    }

    requests.patch(url, headers=headers, json=payload)
