# [ACTIVE] VELOS Notion 동기화 시스템 - Notion 상태 동기화 스크립트
# -*- coding: utf-8 -*-
import os
import requests

NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
DB_ID = os.getenv("NOTION_DATABASE_ID", "")


def update_status(page_id: str, status: str):
    if not (NOTION_TOKEN and page_id):
        return False
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    data = {"properties": {"상태": {"status": {"name": status}}}}
    r = requests.patch(url, headers=headers, json=data, timeout=15)
    return r.ok



