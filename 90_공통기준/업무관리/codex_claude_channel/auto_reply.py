#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paste a bridge message into the visible Claude or Codex app window.

Usage:
    python auto_reply.py "[Codex 완료] ..."
    python auto_reply.py --target codex "[Claude 위임] ..."

Exit codes:
    0: paste + Enter submitted and verified where supported
    1: failed before submission
    2: argparse usage or invalid argument error
    10: existing draft text detected after retries, so paste was skipped
    11: paste succeeded but Enter did not clear the input
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
LOG_PATH = BASE_DIR / "auto_reply.log"
MAX_SKIP_RETRIES = 2
SKIP_RETRY_DELAY_SEC = 5

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_ARGPARSE = 2
EXIT_SKIP_FINAL = 10
EXIT_ENTER_FAILED = 11
RETRY_SKIP = -10

EXIT_CODE_HELP = """Exit codes:
  0   PASS
  1   FAIL (window lookup, paste, or unexpected runtime failure)
  2   argparse usage or invalid argument error
  10  SKIP_FINAL (existing draft text remained after retries)
  11  ENTER_FAILED (paste succeeded, but Enter did not clear the input)
"""

CODEX_REPLY_REMINDER = """---
[필수 회신] 작업 완료 시 즉시:
python 90_공통기준/업무관리/codex_claude_channel/auto_reply.py --target claude "[Codex 완료] <한 줄 요약>"
- 실패 시 require_escalated 1회 재시도
- 그래도 실패면 90_공통기준/업무관리/검토기록/runs/<YYYYMMDD_task-slug>/review.md 작성으로 fallback"""

REQUIRED_PACKAGES = {
    "pyautogui": "pyautogui",
    "pyperclip": "pyperclip",
    "pygetwindow": "pygetwindow",
    "win32gui": "pywin32",
    "psutil": "psutil",
}


@dataclass
class TargetSpec:
    key: str
    label: str
    title_keyword: str
    process_names: tuple[str, ...]
    input_y_ratio: float


@dataclass
class TargetWindow:
    hwnd: int
    title: str
    process_name: str
    rect: tuple[int, int, int, int]
    z_index: int
    is_foreground: bool
    process_match: bool


TARGETS = {
    "claude": TargetSpec(
        key="claude",
        label="Claude",
        title_keyword="claude",
        process_names=("claude.exe",),
        input_y_ratio=0.955,
    ),
    "codex": TargetSpec(
        key="codex",
        label="Codex",
        title_keyword="codex",
        process_names=("codex.exe",),
        input_y_ratio=0.925,
    ),
}


def _log(
    target: str,
    result: str,
    message: str,
    detail: str = "",
    hwnd: int | None = None,
    retries: int = 0,
    verify: str = "paste_only",
) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    rec = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "target": target,
        "result": result,
        "message_len": len(message),
        "detail": detail,
        "hwnd": hwnd,
        "retries": retries,
        "verify": verify,
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _install_missing() -> None:
    missing_packages: list[str] = []
    for module_name, package_name in REQUIRED_PACKAGES.items():
        if importlib.util.find_spec(module_name) is None and package_name not in missing_packages:
            missing_packages.append(package_name)
    if not missing_packages:
        return
    cmd = [sys.executable, "-m", "pip", "install", *missing_packages]
    subprocess.check_call(cmd)


def _process_name_for_hwnd(hwnd: int) -> str:
    try:
        import psutil
        import win32process

        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return psutil.Process(pid).name()
    except Exception:
        return ""


def _matches_target(spec: TargetSpec, title: str, process_name: str) -> tuple[bool, bool]:
    title_match = spec.title_keyword in title.lower()
    process_match = process_name.lower() in spec.process_names
    return title_match or process_match, process_match


def _target_process_summaries(target: str) -> list[str]:
    import psutil

    spec = TARGETS[target]
    summaries: list[str] = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            name = proc.info.get("name") or ""
            if name.lower() in spec.process_names:
                summaries.append(f"{name}:{proc.info.get('pid')}")
        except Exception:
            continue
    return summaries


def _visible_top_window_count() -> int:
    import win32gui

    count = 0

    def enum_cb(hwnd: int, _param: object) -> bool:
        nonlocal count
        if not win32gui.IsWindowVisible(hwnd):
            return True
        try:
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        except Exception:
            return True
        if right > left and bottom > top:
            count += 1
        return True

    win32gui.EnumWindows(enum_cb, None)
    return count


def _window_not_found_message(target: str) -> str:
    label = TARGETS[target].label
    processes = _target_process_summaries(target)
    visible_count = _visible_top_window_count()
    if processes and visible_count == 0:
        return (
            f"{label} window not found; GUI_ACCESS_UNAVAILABLE: no visible top-level windows "
            f"are visible to this process while {label} processes exist ({len(processes)}). "
            "In Codex shell, rerun auto_reply.py with sandbox_permissions=require_escalated."
        )
    if processes:
        return (
            f"{label} window not found; {label} processes exist ({len(processes)}) but no matching "
            "visible window was found. Restore/open the app window, then retry."
        )
    return f"{label} window not found; {label} process not found"


def _append_codex_reply_reminder(message: str, target: str) -> str:
    if target != "codex" or CODEX_REPLY_REMINDER in message:
        return message
    separator = "\n" if message.endswith("\n") else "\n\n"
    return f"{message}{separator}{CODEX_REPLY_REMINDER}"


def _candidate_windows(target: str) -> list[TargetWindow]:
    import win32gui

    spec = TARGETS[target]
    foreground = win32gui.GetForegroundWindow()
    candidates: list[TargetWindow] = []

    def enum_cb(hwnd: int, _param: object) -> bool:
        if not win32gui.IsWindowVisible(hwnd):
            return True
        title = win32gui.GetWindowText(hwnd) or ""
        process_name = _process_name_for_hwnd(hwnd)
        matched, process_match = _matches_target(spec, title, process_name)
        if not matched:
            return True
        try:
            rect = tuple(win32gui.GetWindowRect(hwnd))
        except Exception:
            return True
        left, top, right, bottom = rect
        if right <= left or bottom <= top:
            return True
        candidates.append(
            TargetWindow(
                hwnd=hwnd,
                title=title,
                process_name=process_name,
                rect=rect,
                z_index=len(candidates),
                is_foreground=(hwnd == foreground),
                process_match=process_match,
            )
        )
        return True

    win32gui.EnumWindows(enum_cb, None)
    return candidates


def _select_window(target: str) -> TargetWindow:
    candidates = _candidate_windows(target)
    if not candidates:
        raise RuntimeError(_window_not_found_message(target))

    def score(win: TargetWindow) -> tuple[int, int, int, int]:
        left, top, right, bottom = win.rect
        area = (right - left) * (bottom - top)
        foreground = 1 if win.is_foreground else 0
        process_match = 1 if win.process_match else 0
        # EnumWindows is already top-to-bottom z-order on Windows; lower index wins.
        return (foreground, process_match, -win.z_index, area)

    return sorted(candidates, key=score, reverse=True)[0]


def _client_input_point(hwnd: int, target: str) -> tuple[int, int]:
    import win32gui

    spec = TARGETS[target]
    left_top = win32gui.ClientToScreen(hwnd, (0, 0))
    client_left, client_top = left_top
    _, _, width, height = win32gui.GetClientRect(hwnd)
    return int(client_left + width * 0.50), int(client_top + height * spec.input_y_ratio)


def _activate(hwnd: int) -> None:
    import win32con
    import win32gui

    try:
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        try:
            import pygetwindow

            for win in pygetwindow.getAllWindows():
                if getattr(win, "_hWnd", None) == hwnd:
                    try:
                        win.activate()
                    except Exception:
                        pass
                    break
        except Exception:
            pass
    time.sleep(0.4)


def _draft_text_or_empty() -> str:
    import pyautogui
    import pyperclip

    marker = f"__codex_empty_probe_{uuid.uuid4().hex}__"
    pyperclip.copy(marker)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    pyautogui.hotkey("ctrl", "c")
    time.sleep(0.2)
    copied = pyperclip.paste()
    if copied == marker:
        return ""
    return copied or ""


def _click_input(hwnd: int, target: str) -> None:
    import pyautogui

    x, y = _client_input_point(hwnd, target)
    pyautogui.click(x, y)
    time.sleep(0.2)


def _verify_enter_result(hwnd: int, target: str, message: str) -> tuple[int, str, str]:
    """Return (exit_code, verify_label, detail) after Enter.

    Electron apps usually do not expose a native EditControl, so clipboard
    probing is the practical fallback. If the probe looks like page text rather
    than the composer draft, treat verification as unsupported instead of
    raising a false ENTER_FAILED.
    """
    try:
        _click_input(hwnd, target)
        remaining = _draft_text_or_empty()
    except Exception as exc:
        return EXIT_PASS, "skipped", f"verify=skipped {type(exc).__name__}: {exc}"

    stripped = (remaining or "").strip()
    if not stripped:
        return EXIT_PASS, "enter_confirmed", "verify=enter_confirmed"

    message_text = message.strip()
    plausible_draft_len = max(len(message_text) * 2, 500)
    if len(stripped) <= plausible_draft_len and message_text in stripped:
        return EXIT_ENTER_FAILED, "enter_confirmed", f"draft_len={len(stripped)}"

    return EXIT_PASS, "skipped", f"verify=skipped non_composer_selection_len={len(stripped)}"


def _attempt_send_once(
    message: str,
    target: str,
    win: TargetWindow,
    original_clipboard: str,
    retries: int,
) -> int:
    import pyautogui
    import pyperclip

    _activate(win.hwnd)
    _click_input(win.hwnd, target)

    existing = _draft_text_or_empty()
    if existing.strip():
        _log(
            target,
            "SKIP_EXISTING_TEXT",
            message,
            f"draft_len={len(existing)}",
            win.hwnd,
            retries=retries,
            verify="skipped",
        )
        pyperclip.copy(original_clipboard)
        return RETRY_SKIP

    pyperclip.copy(message)
    pyautogui.hotkey("ctrl", "v")
    # paste 대기: 긴 메시지(Electron 렌더 지연) 대응. 0.5s base + 500자당 0.25s, 상한 5s.
    paste_wait = min(5.0, 0.5 + (len(message) / 500.0) * 0.25)
    time.sleep(paste_wait)
    # 전송: Codex 앱은 멀티라인일 때 Enter=줄바꿈, Ctrl+Enter=전송 (issue #6307).
    # Claude 앱도 Ctrl+Enter 전송 지원. 단일 규칙으로 통일.
    pyautogui.hotkey("ctrl", "enter")
    time.sleep(0.5)

    code, verify, detail = _verify_enter_result(win.hwnd, target, message)
    if code == EXIT_ENTER_FAILED:
        _log(target, "ENTER_FAILED", message, detail, win.hwnd, retries=retries, verify=verify)
        pyperclip.copy(original_clipboard)
        return EXIT_ENTER_FAILED

    _log(target, "PASS", message, f"title={win.title}; {detail}", win.hwnd, retries=retries, verify=verify)
    pyperclip.copy(original_clipboard)
    return EXIT_PASS


def send(message: str, target: str = "claude") -> int:
    if not message.strip():
        raise ValueError("message is empty")
    if target not in TARGETS:
        raise ValueError(f"unsupported target: {target}")
    message = _append_codex_reply_reminder(message, target)

    _install_missing()
    import pyautogui
    import pyperclip

    pyautogui.PAUSE = 0.08
    win = None
    original_clipboard = ""

    try:
        win = _select_window(target)
        original_clipboard = pyperclip.paste()
        for retries in range(MAX_SKIP_RETRIES + 1):
            code = _attempt_send_once(message, target, win, original_clipboard, retries)
            if code != RETRY_SKIP:
                return code
            if retries < MAX_SKIP_RETRIES:
                time.sleep(SKIP_RETRY_DELAY_SEC)

        _log(
            target,
            "SKIP_FINAL",
            message,
            f"retries={MAX_SKIP_RETRIES}",
            win.hwnd,
            retries=MAX_SKIP_RETRIES,
            verify="skipped",
        )
        pyperclip.copy(original_clipboard)
        return EXIT_SKIP_FINAL
    except Exception as exc:
        _log(
            target,
            "FAIL",
            message,
            f"{type(exc).__name__}: {exc}",
            win.hwnd if win else None,
            verify="paste_only",
        )
        try:
            pyperclip.copy(original_clipboard)
        except Exception:
            pass
        raise


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Paste a message into Claude or Codex and press Enter.",
        epilog=EXIT_CODE_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--target", choices=sorted(TARGETS), default="claude")
    parser.add_argument("message", nargs="?")
    args = parser.parse_args(argv[1:])

    if not args.message:
        parser.print_usage(sys.stderr)
        return EXIT_FAIL
    try:
        code = send(args.message, target=args.target)
        if code == EXIT_PASS:
            print(f"PASS: target={args.target} paste+enter submitted", file=sys.stderr)
        elif code == EXIT_SKIP_FINAL:
            print(f"SKIP_FINAL: target={args.target} existing draft text detected after retries", file=sys.stderr)
        elif code == EXIT_ENTER_FAILED:
            print(f"ENTER_FAILED: target={args.target} text remained after Enter", file=sys.stderr)
        return code
    except Exception as exc:
        print(f"FAIL: target={args.target} {type(exc).__name__}: {exc}", file=sys.stderr)
        return EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main(sys.argv))
