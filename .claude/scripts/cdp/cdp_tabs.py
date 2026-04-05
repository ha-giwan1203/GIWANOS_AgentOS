#!/usr/bin/env python3
"""CDP: 열린 탭 목록 반환"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from cdp_common import base_parser, DEFAULT_BROWSER_URL
from playwright.sync_api import sync_playwright

def main():
    p = base_parser("열린 탭 목록 조회")
    args = p.parse_args()

    pw = sync_playwright().start()
    try:
        browser = pw.chromium.connect_over_cdp(args.browser_url, timeout=args.timeout)
    except Exception as e:
        print(f"[ERROR] CDP 연결 실패: {e}", file=sys.stderr)
        pw.stop()
        sys.exit(1)

    contexts = browser.contexts
    if not contexts:
        print("열린 탭 없음")
        pw.stop()
        return

    pages = contexts[0].pages
    for i, pg in enumerate(pages):
        try:
            title = pg.title()
        except Exception:
            title = "(title unavailable)"
        print(f"[{i}] {title}")
        print(f"    {pg.url}")

    print(f"\ntotal: {len(pages)} tabs")
    pw.stop()

if __name__ == "__main__":
    main()
