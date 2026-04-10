#!/usr/bin/env python3
"""프로젝트에서 최상단(최신) 토론 채팅방을 자동 탐지하여 debate_chat_url에 저장한다.

토론모드 진입 전 반드시 이 스크립트를 실행하여 올바른 방으로 진입한다.
세션 간 stale URL 재사용을 방지하는 코드 강제 장치.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
STATE_FILE = PROJECT_ROOT / ".claude" / "state" / "debate_chat_url"

# 프로젝트 ID (slug 무관, ID 부분만 매칭)
PROJECT_ID = "g-p-69bca228f9288191869d502d2056062c"
PROJECT_URL = (
    "https://chatgpt.com/g/"
    "g-p-69bca228f9288191869d502d2056062c-gpt-keulrodeu-eobmu-jadonghwa-toron/project"
)


def detect(browser_url: str = "http://localhost:9222", timeout: int = 30) -> dict:
    """프로젝트 페이지에서 최상단 채팅방 URL을 탐지한다."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"status": "error", "reason": "playwright not installed"}

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(browser_url)
        except Exception as e:
            return {"status": "error", "reason": f"CDP connect failed: {e}"}

        page = browser.contexts[0].pages[0]

        # 프로젝트 페이지 이동
        page.goto(PROJECT_URL, wait_until="domcontentloaded", timeout=timeout * 1000)
        time.sleep(4)

        # 프로젝트 채팅방 링크만 추출 (프로젝트 ID + /c/ 패턴)
        links = page.evaluate(
            f"""() => {{
            const results = [];
            document.querySelectorAll('a').forEach(a => {{
                if (a.href && a.href.includes('{PROJECT_ID}') && a.href.includes('/c/')) {{
                    const text = (a.innerText || a.textContent || '').trim();
                    results.push({{href: a.href, text: text.slice(0, 80)}});
                }}
            }});
            return results;
        }}"""
        )

        if not links:
            return {"status": "error", "reason": "no project chat rooms found"}

        top_url = links[0]["href"]
        top_title = links[0]["text"].split("\n")[0][:60]

        # 일반 채팅 URL 검증 (프로젝트 slug 필수)
        if PROJECT_ID not in top_url:
            return {
                "status": "error",
                "reason": f"URL missing project ID: {top_url[:80]}",
            }

        # debate_chat_url 저장
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(top_url, encoding="utf-8")

        return {
            "status": "ok",
            "url": top_url,
            "title": top_title,
            "total_rooms": len(links),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect latest debate chat room")
    parser.add_argument("--browser-url", default="http://localhost:9222")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--navigate", action="store_true",
                        help="After detection, navigate to the room")
    args = parser.parse_args()

    result = detect(args.browser_url, args.timeout)
    print(json.dumps(result, ensure_ascii=False))

    if result["status"] != "ok":
        return 1

    if args.navigate:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(args.browser_url)
            page = browser.contexts[0].pages[0]
            page.goto(result["url"], wait_until="domcontentloaded", timeout=30000)
            time.sleep(4)
            print(json.dumps({"navigated": True, "current_url": page.url[:100]},
                             ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
