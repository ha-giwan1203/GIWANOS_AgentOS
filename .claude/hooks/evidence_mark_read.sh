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

# Windows 경로 정규화: 백슬래시 → 슬래시 (경로별 정밀 매칭용)
NORM_TEXT="$(echo "$TEXT" | sed 's/\\\\/\//g')"

# 도메인/기준 문서 읽기
echo "$NORM_TEXT" | grep -qE 'SKILL\.md' && mark "skill_read"
echo "$NORM_TEXT" | grep -qE '(^|/|\\)CLAUDE\.md' && mark "domain_read"
echo "$NORM_TEXT" | grep -qE 'TASKS\.md' && mark "tasks_read"
echo "$NORM_TEXT" | grep -qE 'HANDOFF\.md' && mark "handoff_read"
echo "$NORM_TEXT" | grep -qE 'STATUS\.md' && mark "status_read"

# 토론모드 전용 마커 (경로 정밀 매칭)
INSTRUCTION_DIR="$PROJECT_ROOT/.claude/state/instruction_reads"
mkdir -p "$INSTRUCTION_DIR"

if echo "$NORM_TEXT" | grep -qE '토론모드/ENTRY\.md'; then
  : > "$INSTRUCTION_DIR/debate_entry_read.ok"
  hook_log "PostToolUse/evidence_mark_read" "instruction_mark=debate_entry_read"
fi

if echo "$NORM_TEXT" | grep -qE '토론모드/CLAUDE\.md'; then
  : > "$INSTRUCTION_DIR/debate_claude_read.ok"
  hook_log "PostToolUse/evidence_mark_read" "instruction_mark=debate_claude_read"
fi

# 전용 진단 스크립트 성공 흔적
echo "$TEXT" | grep -qE 'date_check(\.sh)?' && mark "date_check"
echo "$TEXT" | grep -qE 'auth_diag(\.sh)?' && mark "auth_diag"
echo "$TEXT" | grep -qE 'identifier_ref_check(\.sh)?|기준정보 대조|identifier_ref' && mark "identifier_ref"

# 문서 갱신 흔적
echo "$TEXT" | grep -qE 'TASKS\.md' && echo "$TEXT" | grep -qE '(Write|Edit|MultiEdit|file_path|path)' && mark "tasks_updated"
echo "$TEXT" | grep -qE 'HANDOFF\.md' && echo "$TEXT" | grep -qE '(Write|Edit|MultiEdit|file_path|path)' && mark "handoff_updated"

exit 0
