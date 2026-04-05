#!/usr/bin/env python3
"""CDP: 특정 탭에서 URL 이동"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from cdp_common import base_parser, connect_and_pick, cleanup

def main():
    p = base_parser("탭에서 URL 이동")
    p.add_argument("url", help="이동할 URL")
    args = p.parse_args()

    pw, browser, page = connect_and_pick(args)
    try:
        page.goto(args.url, timeout=args.timeout)
        print(f"done: {page.title()}")
        print(f"URL: {page.url}")
    except Exception as e:
        print(f"[ERROR] 이동 실패: {e}", file=sys.stderr)
        cleanup(pw)
        sys.exit(1)

    cleanup(pw)

if __name__ == "__main__":
    main()
