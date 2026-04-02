#!/usr/bin/env bash
# PostToolUse(Edit|Write|Bash) hook — dirty.flag 생성
# 구현 파일 변경 감지 시 dirty.flag를 생성하여 검증 필요 상태를 표시
# GPT 합의 2026-04-01: 1단계 구조적 가드레일
set -euo pipefail

ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
TMP_INPUT="$(mktemp)"
cat > "$TMP_INPUT"

python3 - "$ROOT" "$TMP_INPUT" <<'PY'
import json
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1]).resolve()
input_path = pathlib.Path(sys.argv[2])

payload = json.loads(input_path.read_text(encoding="utf-8"))
tool_name = payload.get("tool_name", "")
tool_input = payload.get("tool_input", {})

state_dir = root / "90_공통기준" / "agent-control" / "state"
state_dir.mkdir(parents=True, exist_ok=True)
dirty_flag = state_dir / "dirty.flag"

EXEMPT_SUFFIXES = {
    "request.md",
    "research.md",
    "plan.md",
    "verify.json",
    "HANDOFF.md",
    "TASKS.md",
    "STATUS.md",
    "CLAUDE.md",
}

def normalize_rel(path_str: str) -> str:
    p = pathlib.Path(path_str)
    if not p.is_absolute():
        p = (root / p).resolve()
    try:
        return p.relative_to(root).as_posix()
    except ValueError:
        return p.as_posix()

def is_exempt(rel_path: str) -> bool:
    for suffix in EXEMPT_SUFFIXES:
        if rel_path.endswith(suffix):
            return True
    if ".claude/hooks/" in rel_path:
        return True
    return False

def bash_looks_mutating(command: str) -> bool:
    patterns = [
        r'(^|\s)(cp|mv|rm|touch|mkdir|rmdir|install|ln)\b',
        r'(^|\s)sed\s+.*\s-i(\s|$)',
        r'(^|\s)perl\s+.*\s-i(\s|$)',
        r'(^|\s)python(3)?\s+.*\b(openpyxl|xlsxwriter|xlwings|oletools|olefile|win32com)\b',
        r'(?<!\d)\s*>>?\s',  # 파일 리다이렉트만 (2>&1 제외)
    ]
    return any(re.search(p, command) for p in patterns)

mark_dirty = False

if tool_name in {"Edit", "Write"}:
    file_path = tool_input.get("file_path", "")
    if file_path:
        rel_path = normalize_rel(file_path)
        if not is_exempt(rel_path):
            mark_dirty = True

elif tool_name == "Bash":
    command = tool_input.get("command", "") or ""
    if bash_looks_mutating(command):
        mark_dirty = True

if mark_dirty:
    import time
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    dirty_flag.write_text(f"{ts}\n", encoding="utf-8")
PY

rm -f "$TMP_INPUT"
