#!/usr/bin/env bash
# PreToolUse(Edit|Write|Bash) hook — plan.md 기반 쓰기 허가 게이트
# plan.md 없거나 미승인이면 구현 수정 차단. EXEMPT 파일은 통과.
# GPT 합의 2026-04-01: 1단계 구조적 가드레일
set -euo pipefail
source "$(dirname "$0")/hook_common.sh" 2>/dev/null || true
hook_log "PreToolUse" "pre_write_guard 발화" 2>/dev/null || true

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
current_task_file = state_dir / "current_task"

# plan 없이도 수정 가능한 파일 (운영 문서, 메타 파일)
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

def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }, ensure_ascii=False))
    raise SystemExit(0)

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
    # hooks 자체 수정도 exempt (운영 필요)
    if ".claude/hooks/" in rel_path:
        return True
    return False

def read_current_task_dir():
    if not current_task_file.exists():
        return None
    raw = current_task_file.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    task_dir = (root / raw).resolve() if not pathlib.Path(raw).is_absolute() else pathlib.Path(raw).resolve()
    if not task_dir.exists():
        return None
    return task_dir

def parse_plan(plan_path: pathlib.Path) -> dict:
    text = plan_path.read_text(encoding="utf-8")
    approved = bool(re.search(r'^\s*approved\s*:\s*true\s*$', text, re.I | re.M))
    verify_required = bool(re.search(r'^\s*verify_required\s*:\s*true\s*$', text, re.I | re.M))

    files = []
    in_files = False
    for line in text.splitlines():
        if re.match(r'^\s*files_to_change\s*:\s*$', line):
            in_files = True
            continue
        if in_files:
            if re.match(r'^\s*[A-Za-z_][A-Za-z0-9_]*\s*:\s*', line):
                break
            m = re.match(r'^\s*-\s*(.+?)\s*$', line)
            if m:
                item = m.group(1).strip().strip('"').strip("'")
                files.append(item.replace("\\", "/"))
    return {"approved": approved, "verify_required": verify_required, "files_to_change": files}

def bash_looks_mutating(command: str) -> bool:
    patterns = [
        r'(^|\s)(cp|mv|rm|touch|mkdir|rmdir|install|ln)\b',
        r'(^|\s)sed\s+.*\s-i(\s|$)',
        r'(^|\s)perl\s+.*\s-i(\s|$)',
        r'(^|\s)python(3)?\s+.*\b(openpyxl|xlsxwriter|xlwings|oletools|olefile|win32com)\b',
        r'(?<!\d)\s*>>?\s',  # 파일 리다이렉트만 (2>&1 제외)
    ]
    return any(re.search(p, command) for p in patterns)

# === 메인 로직 ===

# current_task가 설정되지 않았으면 plan 게이트 비활성 (일반 작업)
task_dir = read_current_task_dir()
if task_dir is None:
    raise SystemExit(0)

if tool_name in {"Edit", "Write"}:
    file_path = tool_input.get("file_path", "")
    if not file_path:
        raise SystemExit(0)

    rel_path = normalize_rel(file_path)
    if is_exempt(rel_path):
        raise SystemExit(0)

    plan_path = task_dir / "plan.md"
    if not plan_path.exists():
        deny("plan.md 없는 구현 수정 차단: plan.md 를 먼저 작성하세요.")

    plan = parse_plan(plan_path)
    if not plan["approved"]:
        deny("plan.md 승인 전 구현 금지: approved: true 로 전환 후 다시 시도하세요.")

    allowed = {p.replace("\\", "/") for p in plan["files_to_change"]}
    if rel_path not in allowed:
        deny(f"plan.md 범위 밖 수정 차단: {rel_path}")

    raise SystemExit(0)

if tool_name == "Bash":
    command = tool_input.get("command", "") or ""
    if not bash_looks_mutating(command):
        raise SystemExit(0)

    plan_path = task_dir / "plan.md"
    if not plan_path.exists():
        deny("plan.md 없는 파일 변경성 Bash 차단.")

    plan = parse_plan(plan_path)
    if not plan["approved"]:
        deny("plan.md 승인 전 파일 변경성 Bash 금지.")

    # Bash는 파일 경로 매칭이 불완전하므로 경고만 로깅
    raise SystemExit(0)

raise SystemExit(0)
PY

rm -f "$TMP_INPUT"
