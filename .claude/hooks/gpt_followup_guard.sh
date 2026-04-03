#!/usr/bin/env bash
# PostToolUse + Stop 겸용 — GPT 응답 읽기 후 후속 작업 없이 종료 차단
# PostToolUse: GPT 읽기 감지 → pending.flag 생성 / 후속 작업 감지 → flag 삭제
# Stop: pending.flag 존재 시 block (예외: timeout/로그인/네트워크/검토만)
# GPT 합의 2026-04-01: 토론모드 루프 강제 장치
set -euo pipefail
source "$(dirname "$0")/hook_common.sh" 2>/dev/null || true
hook_log "PostToolUse/Stop" "gpt_followup_guard 발화" 2>/dev/null || true

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
tool_name = payload.get("tool_name", "") or ""
tool_input = payload.get("tool_input", {}) or {}
last_msg = payload.get("last_assistant_message", "") or ""
stop_hook_active = bool(payload.get("stop_hook_active", False))

state_dir = root / "90_공통기준" / "agent-control" / "state"
state_dir.mkdir(parents=True, exist_ok=True)
pending_flag = state_dir / "gpt_followup_pending.flag"

def dump_text(obj) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False)
    except Exception:
        return str(obj)

def set_pending(reason: str) -> None:
    pending_flag.write_text(reason + "\n", encoding="utf-8")

def clear_pending() -> None:
    try:
        pending_flag.unlink()
    except FileNotFoundError:
        pass

def is_post_tool_use() -> bool:
    return bool(tool_name)

def is_stop() -> bool:
    return "last_assistant_message" in payload

def text_contains_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text, re.I) for p in patterns)

def deny_stop(reason: str) -> None:
    print(json.dumps({
        "decision": "block",
        "reason": reason
    }, ensure_ascii=False))
    raise SystemExit(0)

def is_gpt_read_action(tool_name: str, tool_input: dict) -> bool:
    tname = tool_name.lower()
    text = dump_text(tool_input)

    # javascript_tool로 GPT assistant 메시지 읽기
    js_read_patterns = [
        r"data-message-author-role.*assistant",
        r"innertext",
        r"textcontent",
    ]
    if "javascript" in tname:
        if any(re.search(p, text, re.I) for p in js_read_patterns):
            # 전송(send-button click)은 읽기가 아님
            if re.search(r"send-button", text, re.I) and re.search(r"\.click\(", text, re.I):
                return False
            # 입력(insertText)도 읽기가 아님
            if re.search(r"inserttext", text, re.I):
                return False
            return True

    # get_page_text / read_page로 GPT 페이지 읽기
    if "get_page_text" in tname or "read_page" in tname:
        return True

    return False

def is_gpt_send_action(tool_name: str, tool_input: dict) -> bool:
    tname = tool_name.lower()
    text = dump_text(tool_input)

    js_send_patterns = [
        r"send-button",
        r"\.click\(",
    ]
    js_input_patterns = [
        r"prompt-textarea",
        r"execcommand\(['\"]inserttext['\"]",
        r"inputevent\(['\"]input['\"]",
    ]

    if "javascript" in tname:
        if all(re.search(p, text, re.I) for p in js_send_patterns):
            return True
        if any(re.search(p, text, re.I) for p in js_input_patterns):
            return True
    return False

def is_real_followup_work(tool_name: str, tool_input: dict) -> bool:
    if tool_name in {"Bash", "Edit", "Write"}:
        return True
    return False

def looks_like_exception_report(msg: str) -> bool:
    patterns = [
        r"timeout",
        r"타임아웃",
        r"로그인 만료",
        r"재로그인",
        r"네트워크 오류",
        r"검토만",
        r"읽기만",
        r"예외 종료",
    ]
    return text_contains_any(msg, patterns)

# -------------------------
# PostToolUse branch
# -------------------------
if is_post_tool_use():
    # GPT 응답 읽기 감지 → pending flag 생성
    if is_gpt_read_action(tool_name, tool_input):
        set_pending("gpt_response_read")
        raise SystemExit(0)

    # GPT 재입력/전송 감지 → pending flag 삭제
    if is_gpt_send_action(tool_name, tool_input):
        clear_pending()
        raise SystemExit(0)

    # 실제 후속 작업(Bash/Edit/Write) → pending flag 삭제
    if is_real_followup_work(tool_name, tool_input):
        clear_pending()
        raise SystemExit(0)

    raise SystemExit(0)

# -------------------------
# Stop branch
# -------------------------
if is_stop():
    if stop_hook_active:
        raise SystemExit(0)

    if not pending_flag.exists():
        raise SystemExit(0)

    if looks_like_exception_report(last_msg):
        clear_pending()
        raise SystemExit(0)

    deny_stop("GPT 응답을 읽은 뒤 후속 작업 없이 사용자 보고로 종료할 수 없습니다. 반박/재전송 또는 합의된 실행을 먼저 진행하세요.")

raise SystemExit(0)
PY

rm -f "$TMP_INPUT"
