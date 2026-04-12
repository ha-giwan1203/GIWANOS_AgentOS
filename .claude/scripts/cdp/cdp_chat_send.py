#!/usr/bin/env python3
"""CDP: ChatGPT composer에 텍스트를 안전하게 전송."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from cdp_common import base_parser, connect_and_pick, cleanup  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_GATE_FILE = PROJECT_ROOT / ".claude" / "state" / "send_gate_passed"
DEBATE_CHAT_URL_FILE = PROJECT_ROOT / ".claude" / "state" / "debate_chat_url"

LAST_SNIPPET_LIMIT = 200


def load_text(args: argparse.Namespace) -> str:
    if args.text_file:
        return Path(args.text_file).read_text(encoding="utf-8")
    if args.text is not None:
        return args.text
    raise SystemExit("--text 또는 --text-file 중 하나는 필요합니다.")


def last_assistant_snippet(page) -> str:
    return page.evaluate(
        f"""() => {{
          const msgs = [...document.querySelectorAll('[data-message-author-role="assistant"]')];
          const last = msgs[msgs.length - 1];
          return last ? (last.innerText || '').slice(0, {LAST_SNIPPET_LIMIT}) : '';
        }}"""
    )


def is_generating(page) -> bool:
    return bool(
        page.evaluate(
            """() => !!document.querySelector('[data-testid="stop-button"]')"""
        )
    )


def insert_text(page, text: str) -> dict[str, str]:
    """prompt-textarea에 텍스트 삽입. contenteditable DIV는 Playwright type()으로 처리."""
    tag_name = page.evaluate(
        """() => {
          const el = document.querySelector('#prompt-textarea');
          if (!el) return null;
          el.focus();
          return el.tagName;
        }"""
    )
    if not tag_name:
        return {"status": "no_textarea"}

    if tag_name == "TEXTAREA":
        # legacy TEXTAREA 경로: React setter + InputEvent
        page.evaluate(
            """(text) => {
              const el = document.querySelector('#prompt-textarea');
              const proto = Object.getPrototypeOf(el);
              const valueSetter =
                Object.getOwnPropertyDescriptor(proto, 'value')?.set ||
                Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value')?.set;
              valueSetter.call(el, text);
              el.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: text }));
              el.dispatchEvent(new Event('change', { bubbles: true }));
            }""",
            text,
        )
    else:
        # contenteditable DIV 경로: CDP Input.insertText로 React 상태 동기화
        el = page.locator("#prompt-textarea")
        el.click()
        time.sleep(0.3)
        page.keyboard.press("Control+a")
        page.keyboard.press("Delete")
        time.sleep(0.2)
        page.keyboard.insert_text(text)
        time.sleep(0.3)

    return {"status": "inserted", "tagName": tag_name}


def wait_and_click_submit(page, timeout_ms: int) -> dict[str, str]:
    deadline = time.time() + (timeout_ms / 1000)
    while time.time() < deadline:
        result = page.evaluate(
            """() => {
              const btn = document.querySelector('[data-testid="send-button"], #composer-submit-button');
              if (!btn) {
                return { status: 'missing' };
              }
              if (btn.disabled || btn.getAttribute('aria-disabled') === 'true') {
                return { status: 'disabled' };
              }
              const selector = btn.id ? `#${btn.id}` : (btn.getAttribute('data-testid') || 'unknown');
              btn.click();
              return { status: 'clicked', selector };
            }"""
        )
        if result["status"] == "clicked":
            return result
        time.sleep(0.15)
    return {"status": "timeout"}


def verify_sent(page, pre_user_count: int, timeout_s: float = 5.0) -> bool:
    """전송 후 user 메시지 수 증가 또는 GPT 생성 시작으로 검증."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        result = page.evaluate(
            """(preCount) => {
              const userMsgs = document.querySelectorAll('[data-message-author-role="user"]');
              const stopBtn = document.querySelector('[data-testid="stop-button"]');
              const textarea = document.querySelector('#prompt-textarea');
              const composerEmpty = textarea && (textarea.textContent || '').trim().length === 0;
              return {
                userCount: userMsgs.length,
                generating: !!stopBtn,
                composerEmpty: !!composerEmpty,
                increased: userMsgs.length > preCount
              };
            }""",
            pre_user_count,
        )
        # user 메시지 수 증가 OR GPT 생성 시작 OR composer가 비워짐 → 전송 성공
        if result.get("increased") or result.get("generating") or result.get("composerEmpty"):
            return True
        time.sleep(0.5)
    return False


def write_gate_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(int(time.time())), encoding="utf-8")


def main() -> int:
    parser = base_parser("ChatGPT composer에 텍스트 전송")
    parser.add_argument("--text", default=None, help="전송할 텍스트")
    parser.add_argument("--text-file", default=None, help="전송할 UTF-8 텍스트 파일")
    parser.add_argument("--auto-debate-url", action="store_true",
                        help="debate_chat_url 상태 파일에서 URL을 읽어 --match-url-exact로 자동 설정")
    parser.add_argument("--allow-generating", action="store_true", help="기존 응답 생성 중이어도 계속 진행")
    parser.add_argument("--mark-send-gate", action="store_true", help="assistant 최신 읽기 직후 send_gate 파일 갱신")
    parser.add_argument("--gate-file", default=str(DEFAULT_GATE_FILE), help=f"send_gate 파일 경로 (default: {DEFAULT_GATE_FILE})")
    parser.add_argument("--submit-timeout-ms", type=int, default=3000, help="submit button 대기 시간 (default: 3000)")
    parser.add_argument("--dry-run", action="store_true", help="검사만 수행하고 실제 전송은 하지 않음")
    args = parser.parse_args()

    # --auto-debate-url: debate_chat_url 상태 파일에서 URL 자동 설정
    if args.auto_debate_url:
        if not DEBATE_CHAT_URL_FILE.exists():
            print(json.dumps({"status": "error", "reason": "debate_chat_url 파일 없음. debate_room_detect.py --navigate를 먼저 실행하세요."}, ensure_ascii=False))
            return 1
        url = DEBATE_CHAT_URL_FILE.read_text(encoding="utf-8").strip()
        if not url:
            print(json.dumps({"status": "error", "reason": "debate_chat_url 파일이 비어있음"}, ensure_ascii=False))
            return 1
        args.match_url_exact = url

    text = load_text(args)

    if args.dry_run:
        payload = {
            "status": "validated",
            "text_length": len(text),
        }
        print(json.dumps(payload, ensure_ascii=False))
        return 0

    pw, browser, page = connect_and_pick(args)
    try:
        generating = is_generating(page)
        if generating and not args.allow_generating:
            payload = {
                "status": "blocked_generating",
                "reason": "기존 응답 생성 중",
            }
            print(json.dumps(payload, ensure_ascii=False))
            return 3

        last_snippet = last_assistant_snippet(page)

        if args.mark_send_gate:
            write_gate_file(Path(args.gate_file))

        # 전송 전 user 메시지 수 기록 (검증용)
        pre_user_count = page.evaluate(
            """() => document.querySelectorAll('[data-message-author-role="user"]').length"""
        )

        inserted = insert_text(page, text)
        if inserted.get("status") != "inserted":
            print(json.dumps(inserted, ensure_ascii=False))
            return 4

        submit = wait_and_click_submit(page, args.submit_timeout_ms)

        if submit.get("status") == "clicked":
            # 전송 후 user 메시지 수 증가 또는 GPT 생성 시작 검증
            verified = verify_sent(page, pre_user_count, timeout_s=5.0)
            payload = {
                "status": "sent" if verified else "send_unverified",
                "verified": verified,
                "button": submit.get("selector", ""),
                "tagName": inserted.get("tagName", ""),
                "last_assistant_snippet": last_snippet,
            }
            print(json.dumps(payload, ensure_ascii=False))
            return 0 if verified else 6
        else:
            payload = {
                "status": submit.get("status"),
                "verified": False,
                "button": submit.get("selector", ""),
                "tagName": inserted.get("tagName", ""),
                "last_assistant_snippet": last_snippet,
            }
            print(json.dumps(payload, ensure_ascii=False))
            return 5
    finally:
        cleanup(pw)


if __name__ == "__main__":
    raise SystemExit(main())
