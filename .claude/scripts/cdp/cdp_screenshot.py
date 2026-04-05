#!/usr/bin/env python3
"""CDP: 스크린샷 캡처"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from cdp_common import base_parser, connect_and_pick, cleanup

def main():
    p = base_parser("스크린샷 캡처")
    p.add_argument("--output", "-o", default=None,
                    help="저장 경로 (default: /tmp/cdp_screenshot.png)")
    p.add_argument("--full-page", action="store_true",
                    help="전체 페이지 캡처")
    args = p.parse_args()

    output = args.output or os.path.join(os.environ.get("TEMP", "/tmp"), "cdp_screenshot.png")

    pw, browser, page = connect_and_pick(args)
    try:
        page.screenshot(path=output, full_page=args.full_page)
        print(f"저장: {output}")
    except Exception as e:
        print(f"[ERROR] 스크린샷 실패: {e}", file=sys.stderr)
        cleanup(pw)
        sys.exit(1)

    cleanup(pw)

if __name__ == "__main__":
    main()
