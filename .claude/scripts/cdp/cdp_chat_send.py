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

FENCED_CODE_RE = re.compile(r"```.*?```", re.S)
INLINE_CODE_RE = re.compile(r"`[^`]+`")
URL_RE = re.compile(r"https?://\S+")
SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b", re.I)
PATH_RE = re.compile(r"(?:[A-Za-z]:\\[^\s]+|(?:\./|\../|/)[^\s]+)")
FILENAME_RE = re.compile(r"\b[\w.-]+\.(?:py|sh|md|jsonl|json|txt|yml|yaml)\b")
SELECTOR_RE = re.compile(r"(?:\[[^\]]*data-testid[^\]]*\]|#[A-Za-z0-9_-]+|\.[A-Za-z0-9_-]+)")
ERROR_QUOTE_RE = re.compile(r"(?im)^(?:오류 원문|에러 원문)\s*:\s*.+$")
ENGLISH_WORD_RE = re.compile(r"\b[A-Za-z][A-Za-z'-]{1,}\b")
LAST_SNIPPET_LIMIT = 100

# 고유명사/기술 용어 허용 목록 — --require-korean 체크에서 제외
PROPER_NOUN_ALLOWLIST: set[str] = {
    # AI 모델/서비스
    "claude", "gpt", "api", "ai", "anthropic",
    "opus", "sonnet", "haiku",
    # Claude Code 기술 용어
    "context", "compaction", "compact", "hooks", "hook",
    "memory", "handoff", "tasks", "status",
    "precompact", "sessionstart", "sessionend",
    "userpromptsubmit", "pretooluse", "posttooluse",
    "stdout", "stderr", "stdin",
    "resume", "startup", "source",
    "imports", "import", "loading",
    "on-demand", "worktree", "worktrees",
    "read", "write", "edit", "glob", "grep", "bash",
    "github", "git",
    # 파일명 패턴 (확장자 없는 것)
    "claude.md", "tasks.md", "memory.md", "handoff.md", "status.md",
}


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
    tokens = find_forbidden_english(text)
    if not tokens:
        return
    payload = {
        "status": "blocked_language",
        "reason": "한국어 전용 전송 규칙 위반",
        "forbidden_tokens": tokens[:12],
    }
    print(json.dumps(payload, ensure_ascii=False))
    raise SystemExit(2)


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
    parser.add_argument("--expect-last-snippet", default=None, help="직전에 읽은 assistant 최신 답변 일부 기대값")
    parser.add_argument("--expect-last-snippet-file", default=None, help="직전에 읽은 assistant 최신 답변 일부 UTF-8 파일")
    parser.add_argument("--require-korean", action="store_true", help="자연어 영어 포함 시 전송 차단")
    parser.add_argument("--allow-generating", action="store_true", help="기존 응답 생성 중이어도 계속 진행")
    parser.add_argument("--mark-send-gate", action="store_true", help="assistant 최신 읽기 직후 send_gate 파일 갱신")
    parser.add_argument("--gate-file", default=str(DEFAULT_GATE_FILE), help=f"send_gate 파일 경로 (default: {DEFAULT_GATE_FILE})")
    parser.add_argument("--submit-timeout-ms", type=int, default=3000, help="submit button 대기 시간 (default: 3000)")
    parser.add_argument("--dry-run", action="store_true", help="검사만 수행하고 실제 전송은 하지 않음")
    args = parser.parse_args()

    text = load_text(args)
    expected_last_snippet = load_expected_last_snippet(args)
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
