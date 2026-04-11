"""CDP 래퍼 공통 모듈 — Playwright sync API 기반"""

import argparse
import io
import sys
import json
from playwright.sync_api import sync_playwright

# Windows cp949 stdout → UTF-8 강제 (Git Bash 환경에서 한글 깨짐 방지)
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

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
    p.add_argument("--match-url-exact", default=None,
                    help="URL 정확 매칭으로 탭 선택 (trailing slash 정규화)")
    p.add_argument("--match-title", default=None,
                    help="Title 패턴으로 탭 선택 (부분 일치)")
    p.add_argument("--timeout", type=int, default=30000,
                    help="Timeout in ms (default: 30000)")
    return p


def _normalize_url(url: str) -> str:
    """URL 정규화: trailing slash 제거, 소문자화 없음 (경로 대소문자 유지)"""
    return url.rstrip("/")


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

    # 탭 선택: --match-url-exact > --match-url > --match-title > --tab
    # pages[0] 기본 선택 제거 — 반드시 명시적 탭 지정 필요
    page = None
    if args.match_url_exact:
        target = _normalize_url(args.match_url_exact)
        candidates = [p for p in pages if _normalize_url(p.url) == target]
        if len(candidates) == 1:
            page = candidates[0]
        elif len(candidates) == 0:
            print(f"[ERROR] URL 정확 매칭 실패: '{args.match_url_exact}' — 일치 탭 0개", file=sys.stderr)
            pw.stop()
            sys.exit(1)
        else:
            print(f"[ERROR] URL 정확 매칭 모호: '{args.match_url_exact}' — 일치 탭 {len(candidates)}개", file=sys.stderr)
            pw.stop()
            sys.exit(1)
    elif args.match_url:
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
        print("[ERROR] 탭 지정 필수: --match-url-exact, --match-url, --match-title, --tab 중 하나를 사용하세요", file=sys.stderr)
        pw.stop()
        sys.exit(1)

    return pw, browser, page


def cleanup(pw):
    """Playwright 정리"""
    try:
        pw.stop()
    except Exception:
        pass
