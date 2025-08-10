# VELOS 시스템 - Notion 연동 모듈
from modules.core import config
import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# VELOS 경로 기준으로 .env 강제 로드
load_dotenv(dotenv_path="C:/giwanos/.env")

NOTION_API_KEY = os.getenv("NOTION_TOKEN")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")
NOTION_VERSION = "2022-06-28"

def upload_summary_to_notion(summary_path):
    """
    Markdown 요약 파일을 Notion 페이지에 업로드하는 함수.
    """
    if NOTION_API_KEY is None or NOTION_PAGE_ID is None:
        print("❌ Notion API 키 또는 Page ID가 설정되어 있지 않습니다.")
        return False

    try:
        with open(summary_path, "r", encoding="utf-8") as file:
            markdown_content = file.read()

        headers = {
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION
        }

        data = {
            "parent": {"type": "page_id", "page_id": NOTION_PAGE_ID},
            "properties": {
                "title": [
                    {
                        "text": {
                            "content": f"VELOS 요약 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
                        }
                    }
                ]
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": markdown_content[:2000]}}]
                    }
                }
            ]
        }

        response = requests.post("https://api.notion.com/v1/pages", headers=headers, json=data)

        if response.status_code == 200 or response.status_code == 201:
            print("✅ Notion 업로드 완료:", response.json().get("url", "링크 없음"))
            return True
        else:
            print(f"❌ Notion 업로드 실패: {response.status_code}")
            print(response.text)
            return False

    except Exception as e:
        print("❌ 예외 발생 (Notion 업로드):", e)
        return False

# === VELOS shim: make summary_path optional ===
try:
    _velos_orig_upload = upload_summary_to_notion
    def upload_summary_to_notion(summary_path=None, *args, **kwargs):
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        if summary_path is None:
            reports = root / "data" / "reports"
            candidates = []
            if reports.exists():
                candidates += list(reports.glob("weekly_summary_*.md"))
                candidates += list(reports.glob("weekly_report_*.md"))
                candidates += list(reports.glob("summary_dashboard.json"))
            if not candidates:
                raise FileNotFoundError("요약 파일을 찾을 수 없습니다. summary_path를 명시적으로 넘겨주세요.")
            latest = max(candidates, key=lambda p: p.stat().st_mtime)
            summary_path = str(latest)
        return _velos_orig_upload(summary_path, *args, **kwargs)
except Exception:
    pass
# === END shim ===


