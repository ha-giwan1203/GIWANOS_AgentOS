"""
VELOS 운영 철학 선언문
- 파일명 절대 변경 금지 · 모든 수정 후 자가 검증 필수 · 실행 결과 직접 테스트
"""
from __future__ import annotations

import os
import requests
from typing import Any
from modules.core.config import get_setting


class SlackMirror:
    def __init__(self):
        self.token = os.getenv("SLACK_BOT_TOKEN")
        self.channel = os.getenv("SLACK_CHANNEL_ID") or get_setting("SLACK_CHANNEL_ID")
        self.enabled = bool(self.token and self.channel)

    def mirror(self, conversation_id: str, prompt: str, rsp: Any) -> bool:
        if not self.enabled:
            return True
        text = f":link: VELOS ChatSync `{conversation_id}`\n• prompt: `{prompt}`\n• rsp: `{str(rsp)[:2000]}`"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json; charset=utf-8",
        }
        r = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers=headers,
            json={"channel": self.channel, "text": text},
            timeout=15,
        )
        try:
            return r.ok and r.json().get("ok", False)
        except Exception:
            return False


class NotionMirror:
    def __init__(self):
        self.token = os.getenv("NOTION_TOKEN")
        self.page = os.getenv("NOTION_PAGE_ID")
        self.enabled = bool(self.token and self.page)

    def mirror(self, conversation_id: str, prompt: str, rsp: Any) -> bool:
        if not self.enabled:
            return True
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }
        content = f"VELOS ChatSync `{conversation_id}`\n- prompt: {prompt}\n- rsp: {str(rsp)[:3000]}"
        payload = {
            "parent": {"page_id": self.page},
            "properties": {
                "title": {"title": [{"text": {"content": f"ChatSync {conversation_id}"}}]}
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": content}}]},
                }
            ],
        }
        try:
            r = requests.post("https://api.notion.com/v1/pages", headers=headers, json=payload, timeout=20)
            return r.ok
        except Exception:
            return False
