#!/bin/bash
# PostToolUse(Read|Grep|Glob|Bash|Write|Edit|MultiEdit)
# 읽기/검증/문서갱신 증거 마커 적립

source "$(dirname "$0")/hook_common.sh" 2>/dev/null

INPUT="$(cat)"

SESSION_KEY="$(session_key)"
SESSION_DIR="$STATE_EVIDENCE/$SESSION_KEY"
PROOF_DIR="$SESSION_DIR/proofs"
START_FILE="$SESSION_DIR/.session_start"

mkdir -p "$PROOF_DIR"

if [ ! -f "$START_FILE" ]; then
  : > "$START_FILE"
fi

mark() {
  local name="$1"
  : > "$PROOF_DIR/$name.ok"
  hook_log "PostToolUse/evidence_mark_read" "mark=$name"
}

TEXT="$(printf '%s' "$INPUT" | tr '\n' ' ' | sed 's/\\"/"/g')"

# 도메인/기준 문서 읽기
echo "$TEXT" | grep -qE 'SKILL\.md' && mark "skill_read"
echo "$TEXT" | grep -qE '(^|/|\\)CLAUDE\.md' && mark "domain_read"
echo "$TEXT" | grep -qE 'TASKS\.md' && mark "tasks_read"
echo "$TEXT" | grep -qE 'HANDOFF\.md' && mark "handoff_read"
echo "$TEXT" | grep -qE 'STATUS\.md' && mark "status_read"

# 전용 진단 스크립트 성공 흔적
echo "$TEXT" | grep -qE 'date_check(\.sh)?' && mark "date_check"
echo "$TEXT" | grep -qE 'auth_diag(\.sh)?' && mark "auth_diag"
echo "$TEXT" | grep -qE 'identifier_ref_check(\.sh)?|기준정보 대조|identifier_ref' && mark "identifier_ref"

# 문서 갱신 흔적 — tool_name이 Write/Edit/MultiEdit일 때만 갱신 판정
# 이전: 전체 텍스트에서 "Write|Edit|file_path" 문자열 grep → Read/Grep도 오탐
# GPT+Claude 합의 2026-04-10: tool_name 필드를 명시적으로 파싱
TOOL_NAME=""
if type safe_json_get >/dev/null 2>&1; then
  TOOL_NAME=$(printf '%s' "$INPUT" | safe_json_get "tool_name" 2>/dev/null || true)
fi
if [ -z "$TOOL_NAME" ]; then
  TOOL_NAME=$(echo "$TEXT" | sed -n 's/.*"tool_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
fi

IS_WRITE_TOOL="NO"
case "$TOOL_NAME" in
  Write|Edit|MultiEdit) IS_WRITE_TOOL="YES" ;;
esac

if [ "$IS_WRITE_TOOL" = "YES" ]; then
  echo "$TEXT" | grep -qE 'TASKS\.md' && mark "tasks_updated"
  echo "$TEXT" | grep -qE 'HANDOFF\.md' && mark "handoff_updated"
fi

exit 0
