#!/usr/bin/env python3
"""CDP: 페이지 텍스트 추출"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from cdp_common import base_parser, connect_and_pick, cleanup

def main():
    p = base_parser("페이지 텍스트 추출")
    p.add_argument("--selector", default=None,
                    help="특정 요소만 추출 (CSS selector)")
    p.add_argument("--limit", type=int, default=5000,
                    help="출력 글자 수 제한 (default: 5000, 0=무제한)")
    args = p.parse_args()

    pw, browser, page = connect_and_pick(args)
    try:
        if args.selector:
            el = page.query_selector(args.selector)
            text = el.inner_text() if el else f"[ERROR] selector '{args.selector}' 없음"
        else:
            text = page.inner_text("body")

        if args.limit > 0 and len(text) > args.limit:
            text = text[:args.limit] + f"\n...(truncated, total {len(text)} chars)"

        print(text)
    except Exception as e:
        print(f"[ERROR] 읽기 실패: {e}", file=sys.stderr)
        cleanup(pw)
        sys.exit(1)

    cleanup(pw)

if __name__ == "__main__":
    main()
