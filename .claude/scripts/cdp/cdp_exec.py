#!/usr/bin/env python3
"""CDP: JavaScript 실행 후 결과 반환"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from cdp_common import base_parser, connect_and_pick, cleanup

def main():
    p = base_parser("JavaScript 실행")
    p.add_argument("code", help="실행할 JS 코드")
    args = p.parse_args()

    pw, browser, page = connect_and_pick(args)
    try:
        result = page.evaluate(args.code)
        if result is not None:
            print(result)
    except Exception as e:
        print(f"[ERROR] JS 실행 실패: {e}", file=sys.stderr)
        cleanup(pw)
        sys.exit(1)

    cleanup(pw)

if __name__ == "__main__":
    main()
