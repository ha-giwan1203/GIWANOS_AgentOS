#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paste a bridge message into the visible Claude or Codex app window.

Usage:
    python auto_reply.py "[Codex 완료] ..."
    python auto_reply.py --target codex "[Claude 위임] ..."

Exit codes:
    0: paste + Enter submitted
    1: failed before submission
    2: existing draft text detected, so paste was skipped
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


def _log(target: str, result: str, message: str, detail: str = "", hwnd: int | None = None) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    rec = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "target": target,
        "result": result,
        "message_len": len(message),
        "detail": detail,
        "hwnd": hwnd,
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
        raise RuntimeError(f"{TARGETS[target].label} window not found")

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


def send(message: str, target: str = "claude") -> int:
    if not message.strip():
        raise ValueError("message is empty")
    if target not in TARGETS:
        raise ValueError(f"unsupported target: {target}")

    _install_missing()
    import pyautogui
    import pyperclip

    pyautogui.PAUSE = 0.08
    win = _select_window(target)
    original_clipboard = pyperclip.paste()

    try:
        _activate(win.hwnd)
        x, y = _client_input_point(win.hwnd, target)
        pyautogui.click(x, y)
        time.sleep(0.2)

        existing = _draft_text_or_empty()
        if existing.strip():
            _log(target, "SKIP_EXISTING_TEXT", message, f"draft_len={len(existing)}", win.hwnd)
            pyperclip.copy(original_clipboard)
            return 2

        pyperclip.copy(message)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.5)
        pyautogui.press("enter")
        time.sleep(0.2)
        _log(target, "PASS", message, f"title={win.title}", win.hwnd)
        pyperclip.copy(original_clipboard)
        return 0
    except Exception as exc:
        _log(target, "FAIL", message, f"{type(exc).__name__}: {exc}", win.hwnd if "win" in locals() else None)
        try:
            pyperclip.copy(original_clipboard)
        except Exception:
            pass
        raise


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Paste a message into Claude or Codex and press Enter.")
    parser.add_argument("--target", choices=sorted(TARGETS), default="claude")
    parser.add_argument("message", nargs="?")
    args = parser.parse_args(argv[1:])

    if not args.message:
        parser.print_usage(sys.stderr)
        return 1
    try:
        code = send(args.message, target=args.target)
        if code == 0:
            print(f"PASS: target={args.target} paste+enter submitted")
        elif code == 2:
            print(f"SKIP: target={args.target} existing draft text detected", file=sys.stderr)
        return code
    except Exception as exc:
        print(f"FAIL: target={args.target} {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
