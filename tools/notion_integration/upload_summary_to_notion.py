# =============================================
# VELOS: Notion Uploader (path required)
# =============================================
from __future__ import annotations
import os, json
from pathlib import Path
import requests

NOTION_API = "https://api.notion.com/v1/pages"
NOTION_VERSION = "2022-06-28"

def _headers():
    return {
        "Authorization": f"Bearer {os.environ['NOTION_TOKEN']}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

def _parent():
    # 페이지 ID를 부모로 사용
    pid = os.environ.get("NOTION_PAGE_ID")
    if not pid:
        raise RuntimeError("NOTION_PAGE_ID 미설정")
    return {"type": "page_id", "page_id": pid}

def _title_block(title: str):
    return [{"type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": title[:100]}}]}}]

def upload_summary_to_notion(summary_path: str) -> bool:
    p = Path(summary_path)
    if not p.exists():
        raise FileNotFoundError(summary_path)

    title = f"VELOS Report: {p.name}"
    children = _title_block(title)

    if p.suffix.lower() == ".md":
        try:
            txt = p.read_text(encoding="utf-8")[:1900]  # 블록 길이 보호
        except Exception:
            txt = f"(읽기 실패) {p}"
        children.append({"type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": txt}}]}})
    else:
        children.append({"type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": f"로컬 경로: {p}"}}]}})

    payload = {
        "parent": _parent(),
        "properties": {"title": [{"type": "text", "text": {"content": title}}]},
        "children": children,
    }
    r = requests.post(NOTION_API, headers=_headers(), data=json.dumps(payload))
    if r.status_code in (200, 201):
        return True
    raise RuntimeError(f"Notion 업로드 실패: {r.status_code} {r.text}")

if __name__ == "__main__":
    import sys
    print(upload_summary_to_notion(sys.argv[1]))
