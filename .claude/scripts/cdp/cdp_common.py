"""CDP 래퍼 공통 모듈 — Playwright sync API 기반"""

import argparse
import sys
import json
from playwright.sync_api import sync_playwright

DEFAULT_BROWSER_URL = "http://localhost:9222"


def base_parser(description):
    """공통 argparse 파서"""
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--browser-url", default=DEFAULT_BROWSER_URL,
                    help=f"CDP endpoint (default: {DEFAULT_BROWSER_URL})")
    p.add_argument("--tab", type=int, default=None,
                    help="Tab index (0-based)")
    p.add_argument("--match-url", default=None,
                    help="URL 패턴으로 탭 선택 (부분 일치)")
    p.add_argument("--match-title", default=None,
                    help="Title 패턴으로 탭 선택 (부분 일치)")
    p.add_argument("--timeout", type=int, default=30000,
                    help="Timeout in ms (default: 30000)")
    return p


def connect_and_pick(args):
    """CDP 연결 + 탭 선택. (playwright, browser, page) 반환."""
    pw = sync_playwright().start()
    try:
        browser = pw.chromium.connect_over_cdp(args.browser_url, timeout=args.timeout)
    except Exception as e:
        print(f"[ERROR] CDP 연결 실패: {e}", file=sys.stderr)
        pw.stop()
        sys.exit(1)

    contexts = browser.contexts
    if not contexts:
        print("[ERROR] 브라우저 컨텍스트 없음", file=sys.stderr)
        pw.stop()
        sys.exit(1)

    pages = contexts[0].pages
    if not pages:
        print("[ERROR] 열린 탭 없음", file=sys.stderr)
        pw.stop()
        sys.exit(1)

    # 탭 선택: --match-url > --match-title > --tab > 첫 번째
    page = None
    if args.match_url:
        for p in pages:
            if args.match_url in p.url:
                page = p
                break
        if not page:
            print(f"[ERROR] URL 패턴 '{args.match_url}' 일치 탭 없음", file=sys.stderr)
            pw.stop()
            sys.exit(1)
    elif args.match_title:
        for p in pages:
            if args.match_title in p.title():
                page = p
                break
        if not page:
            print(f"[ERROR] Title 패턴 '{args.match_title}' 일치 탭 없음", file=sys.stderr)
            pw.stop()
            sys.exit(1)
    elif args.tab is not None:
        if args.tab >= len(pages):
            print(f"[ERROR] 탭 인덱스 {args.tab} 초과 (총 {len(pages)}개)", file=sys.stderr)
            pw.stop()
            sys.exit(1)
        page = pages[args.tab]
    else:
        page = pages[0]

    return pw, browser, page


def cleanup(pw):
    """Playwright 정리"""
    try:
        pw.stop()
    except Exception:
        pass
