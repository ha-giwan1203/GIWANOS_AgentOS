#!/usr/bin/env python3
"""CDP: ChatGPT composer에 텍스트를 안전하게 전송."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from cdp_common import base_parser, connect_and_pick, cleanup  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_GATE_FILE = PROJECT_ROOT / ".claude" / "state" / "send_gate_passed"
DEBATE_CHAT_URL_FILE = PROJECT_ROOT / ".claude" / "state" / "debate_chat_url"

FENCED_CODE_RE = re.compile(r"```.*?```", re.S)
INLINE_CODE_RE = re.compile(r"`[^`]+`")
URL_RE = re.compile(r"https?://\S+")
SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b", re.I)
PATH_RE = re.compile(r"(?:[A-Za-z]:\\[^\s]+|(?:\./|\../|/)[^\s]+)")
FILENAME_RE = re.compile(r"\b[\w.-]+\.(?:py|sh|md|jsonl|json|txt|yml|yaml)\b")
SELECTOR_RE = re.compile(r"(?:\[[^\]]*data-testid[^\]]*\]|#[A-Za-z0-9_-]+|\.[A-Za-z0-9_-]+)")
ERROR_QUOTE_RE = re.compile(r"(?im)^(?:오류 원문|에러 원문)\s*:\s*.+$")
ENGLISH_WORD_RE = re.compile(r"\b[A-Za-z][A-Za-z'-]{1,}\b")
KOREAN_CHAR_RE = re.compile(r"[\uAC00-\uD7A3]")  # 완성형 한글
# 비허용 영어 단어 비율 임계값: 한글 글자 대비 이 비율 이하면 허용
# 예: 한글 100자, 비허용 영어 5단어 → 5% → 허용
ENGLISH_RATIO_THRESHOLD = 0.15  # 15%
LAST_SNIPPET_LIMIT = 200

# 코어 목록: 외부 파일 로드 실패 시에도 유지되는 최소 허용 목록
_CORE_ALLOWLIST: set[str] = {
    "claude", "gpt", "git", "hook", "hooks", "cdp", "json", "bash",
    "tasks", "handoff", "status", "api", "ai", "anthropic",
    "commit", "push", "merge", "diff", "branch",
}

_ALLOWLIST_FILE = Path(__file__).with_name("korean_allowlist.txt")


def _load_allowlist() -> set[str]:
    """코어 목록 + 외부 파일(korean_allowlist.txt) 가산 merge."""
    result = set(_CORE_ALLOWLIST)
    try:
        for line in _ALLOWLIST_FILE.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                result.add(stripped.lower())
    except (FileNotFoundError, OSError):
        pass  # 파일 없으면 코어만 사용
    return result


PROPER_NOUN_ALLOWLIST: set[str] = _load_allowlist()


def load_text(args: argparse.Namespace) -> str:
    if args.text_file:
        return Path(args.text_file).read_text(encoding="utf-8")
    if args.text is not None:
        return args.text
    raise SystemExit("--text 또는 --text-file 중 하나는 필요합니다.")


def load_expected_last_snippet(args: argparse.Namespace) -> str | None:
    if args.expect_last_snippet and args.expect_last_snippet_file:
        raise SystemExit("--expect-last-snippet 과 --expect-last-snippet-file 중 하나만 사용하세요.")
    if args.expect_last_snippet_file:
        return Path(args.expect_last_snippet_file).read_text(encoding="utf-8")
    return args.expect_last_snippet


def normalize_snippet(text: str | None) -> str:
    if text is None:
        return ""
    return text.replace("\r\n", "\n").strip()


def strip_allowed_literals(text: str) -> str:
    cleaned = FENCED_CODE_RE.sub(" ", text)
    cleaned = INLINE_CODE_RE.sub(" ", cleaned)
    cleaned = ERROR_QUOTE_RE.sub(" ", cleaned)
    cleaned = URL_RE.sub(" ", cleaned)
    cleaned = SHA_RE.sub(" ", cleaned)
    cleaned = PATH_RE.sub(" ", cleaned)
    cleaned = FILENAME_RE.sub(" ", cleaned)
    cleaned = SELECTOR_RE.sub(" ", cleaned)
    cleaned = cleaned.replace("data-testid", " ")
    return cleaned


def find_forbidden_english(text: str) -> list[str]:
    cleaned = strip_allowed_literals(text)
    tokens: list[str] = []
    seen: set[str] = set()
    for match in ENGLISH_WORD_RE.finditer(cleaned):
        token = match.group(0)
        lowered = token.lower()
        if lowered in seen:
            continue
        if lowered in PROPER_NOUN_ALLOWLIST:
            continue
        seen.add(lowered)
        tokens.append(token)
    return tokens


def ensure_korean_only(text: str) -> None:
    """한국어 가드 — 현재 비활성화 (사용자 요청 2026-04-11).
    허용 목록 관리 비용 대비 실효성 낮아 차단 제거.
    향후 재활성화 시 비율 기반(ENGLISH_RATIO_THRESHOLD) 검사 권장."""
    return  # 차단 비활성화


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
    return page.evaluate(
        """(text) => {
          const el = document.querySelector('#prompt-textarea');
          if (!el) {
            return { status: 'no_textarea' };
          }
          el.focus();
          if (el.tagName === 'TEXTAREA') {
            const proto = Object.getPrototypeOf(el);
            const valueSetter =
              Object.getOwnPropertyDescriptor(proto, 'value')?.set ||
              Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value')?.set;
            valueSetter.call(el, text);
            el.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: text }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
          } else {
            document.execCommand('selectAll', false, null);
            document.execCommand('insertText', false, text);
          }
          return {
            status: 'inserted',
            tagName: el.tagName,
          };
        }""",
        text,
    )


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


def write_gate_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(int(time.time())), encoding="utf-8")


def main() -> int:
    parser = base_parser("ChatGPT composer에 텍스트 전송")
    parser.add_argument("--text", default=None, help="전송할 텍스트")
    parser.add_argument("--text-file", default=None, help="전송할 UTF-8 텍스트 파일")
    # --expect-last-snippet / --expect-last-snippet-file 제거 (사용자 지시 2026-04-11)
    # 스니펫 비교가 인코딩/잘림 차이로 오차단을 유발하므로 폐기
    parser.add_argument("--expect-last-snippet", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--expect-last-snippet-file", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--require-korean", action="store_true", help="(비활성화됨) 한국어 가드")
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
    # 스니펫 비교 폐기: 인자가 넘어와도 무시
    expected_last_snippet = None
    if args.require_korean:
        ensure_korean_only(text)

    if args.dry_run:
        payload = {
            "status": "validated",
            "expected_last_snippet": expected_last_snippet is not None,
            "require_korean": args.require_korean,
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
        if expected_last_snippet is not None:
            expected_snippet = normalize_snippet(expected_last_snippet)
            current_snippet = normalize_snippet(last_snippet)
            if current_snippet != expected_snippet:
                payload = {
                    "status": "blocked_reply_changed",
                    "reason": "직전에 확인한 최신 답변이 바뀌어 전송 중단",
                    "expected_last_assistant_snippet": expected_snippet,
                    "current_last_assistant_snippet": current_snippet,
                }
                print(json.dumps(payload, ensure_ascii=False))
                return 6

        if args.mark_send_gate:
            write_gate_file(Path(args.gate_file))

        inserted = insert_text(page, text)
        if inserted.get("status") != "inserted":
            print(json.dumps(inserted, ensure_ascii=False))
            return 4

        submit = wait_and_click_submit(page, args.submit_timeout_ms)
        payload = {
            "status": "sent" if submit.get("status") == "clicked" else submit.get("status"),
            "button": submit.get("selector", ""),
            "tagName": inserted.get("tagName", ""),
            "last_assistant_snippet": last_snippet,
        }
        print(json.dumps(payload, ensure_ascii=False))
        return 0 if submit.get("status") == "clicked" else 5
    finally:
        cleanup(pw)


if __name__ == "__main__":
    raise SystemExit(main())
