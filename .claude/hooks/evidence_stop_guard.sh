#!/bin/bash
# Stop — req 기반으로만 활성. 근거 없는 최종 결론 차단.

source "$(dirname "$0")/hook_common.sh" 2>/dev/null
hook_log "Stop" "evidence_stop_guard 발화" 2>/dev/null

TRANSCRIPT="$CLAUDE_TRANSCRIPT_PATH"
STATE_ROOT="${CLAUDE_PROJECT_DIR:-.}/.claude/state/evidence"

session_key() {
  local seed="${CLAUDE_TRANSCRIPT_PATH:-$PWD}"
  if command -v sha1sum >/dev/null 2>&1; then
    printf '%s' "$seed" | sha1sum | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    printf '%s' "$seed" | shasum | awk '{print $1}'
  else
    printf '%s' "$seed" | cksum | awk '{print $1}'
  fi
}

SESSION_KEY="$(session_key)"
SESSION_DIR="$STATE_ROOT/$SESSION_KEY"
REQ_DIR="$SESSION_DIR/requires"
PROOF_DIR="$SESSION_DIR/proofs"
START_FILE="$SESSION_DIR/.session_start"

mkdir -p "$REQ_DIR" "$PROOF_DIR"

if [ ! -f "$START_FILE" ]; then
  : > "$START_FILE"
fi

fresh_file() {
  local f="$1"
  [ -f "$f" ] && [ "$f" -nt "$START_FILE" ]
}

fresh_req() { fresh_file "$REQ_DIR/$1.req"; }
fresh_ok()  { fresh_file "$PROOF_DIR/$1.ok"; }

has_any_req() {
  find "$REQ_DIR" -maxdepth 1 -type f -name '*.req' -newer "$START_FILE" | grep -q .
}

if [ -z "$TRANSCRIPT" ] || [ ! -f "$TRANSCRIPT" ]; then
  exit 0
fi

if ! has_any_req; then
  exit 0
fi

LAST_ASSISTANT="$(tail -n 120 "$TRANSCRIPT" 2>/dev/null | grep '"type":"assistant"' | tail -n 1)"
if [ -z "$LAST_ASSISTANT" ]; then
  exit 0
fi

LAST_TEXT="$(echo "$LAST_ASSISTANT" | sed 's/\\n/\n/g' | sed -n 's/.*"text"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | tr '\n' ' ')"
if [ -z "$LAST_TEXT" ]; then
  exit 0
fi

block() {
  local reason="$1"
  hook_log "Stop/evidence_stop_guard" "BLOCK: $reason" 2>/dev/null
  hook_incident "hook_block" "evidence_stop_guard" "" "$reason" 2>/dev/null || true
  echo "{\"decision\":\"block\",\"reason\":\"[evidence_stop_guard] $reason\"}"
  exit 2
}

# 1) 로그인 실패/수동 로그인 주장
if fresh_req "auth_diag"; then
  if echo "$LAST_TEXT" | grep -qiE '(로그인 실패|실패로 판단|수동 로그인|직접 로그인 필요|사용자가 로그인)'; then
    if ! fresh_ok "auth_diag"; then
      block "auth_diag.req 존재. auth_diag.ok 없이 로그인 실패/수동 로그인 결론 금지."
    fi
  fi
fi

# 2) 식별자 불일치 주장
if fresh_req "skill_read" || fresh_req "identifier_ref"; then
  if echo "$LAST_TEXT" | grep -qiE '(아이디가 다르|계정이 다르|식별자 불일치|품번 불일치|기준정보와 다르)'; then
    if ! fresh_ok "skill_read" && ! fresh_ok "identifier_ref"; then
      block "skill_read.req / identifier_ref.req 존재. SKILL.md 또는 기준정보 대조 없이 불일치 결론 금지."
    fi
  fi
fi

# 3) 완료/반영 완료/PASS 주장
if fresh_req "tasks_handoff"; then
  if echo "$LAST_TEXT" | grep -qiE '(완료|반영 완료|수정 완료|PASS)'; then
    if ! fresh_ok "tasks_updated" || ! fresh_ok "handoff_updated"; then
      block "tasks_handoff.req 존재. TASKS/HANDOFF 갱신 없이 완료/PASS 결론 금지."
    fi
  fi
fi

exit 0
