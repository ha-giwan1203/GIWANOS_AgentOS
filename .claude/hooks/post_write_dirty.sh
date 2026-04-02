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

PATTERNS = [
    r'(^|\s)(cp|mv|rm|touch|mkdir|rmdir|install|ln)\b',
    r'(^|\s)sed\s+.*\s-i(\s|$)',
    r'(^|\s)perl\s+.*\s-i(\s|$)',
    r'(^|\s)python(3)?\s+.*\b(xlsxwriter|xlwings|oletools|olefile|win32com)\b',
    r'(^|\s)python(3)?\s+.*\bopenpyxl\b.*\bsave\b',  # openpyxl은 save 포함 시만 dirty
    # 리다이렉트: /dev/ /tmp/ /var/tmp/ /proc/ $TMPDIR $TMP $TEMP $TMP_INPUT 계열은 허용
    r'>>?\s+(?!\/dev\/|\/tmp\/|\/var\/tmp\/|\/proc\/|\$TMPDIR|\$TMP_INPUT|\$TMP\b|\$TEMP\b)',
]

def bash_looks_mutating(command: str):
    """첫 번째 매칭 패턴 인덱스와 매칭 텍스트 반환. 없으면 (None, None)."""
    for i, p in enumerate(PATTERNS):
        m = re.search(p, command)
        if m:
            return i, m.group(0)[:100]
    return None, None

mark_dirty = False
matched_info = {}

if tool_name in {"Edit", "Write"}:
    file_path = tool_input.get("file_path", "")
    if file_path:
        rel_path = normalize_rel(file_path)
        if not is_exempt(rel_path):
            mark_dirty = True
            matched_info = {"pattern_idx": "Edit/Write", "matched_text": rel_path[:100], "command": ""}

elif tool_name == "Bash":
    command = tool_input.get("command", "") or ""
    pat_idx, matched_text = bash_looks_mutating(command)
    if pat_idx is not None:
        mark_dirty = True
        matched_info = {"pattern_idx": pat_idx, "matched_text": matched_text, "command": command[:200]}

if mark_dirty:
    import time
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    tool_use_id = payload.get("tool_use_id", "")
    lines = [
        ts,
        f"tool_name={tool_name}",
        f"tool_use_id={tool_use_id}",
        f"matched_pattern={matched_info.get('pattern_idx', '')}",
        f"matched_text={matched_info.get('matched_text', '')}",
        f"command_head={matched_info.get('command', '')}",
    ]
    dirty_flag.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

rm -f "$TMP_INPUT"
