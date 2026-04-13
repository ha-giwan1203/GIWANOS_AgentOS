#!/bin/bash
# PreToolUse(Bash) — GPT 전송 직전 지침 읽기 강제 게이트
# cdp_chat_send.py / share-result / finish 실행 전
# ENTRY.md + 토론모드 CLAUDE.md 읽기 여부 확인
# 미읽기 시 deny+exit 2

source "$(dirname "$0")/hook_common.sh" 2>/dev/null

INPUT="$(cat)"
COMMAND="$(echo "$INPUT" | safe_json_get "command" 2>/dev/null)"

# GPT 전송 관련 명령만 검사
is_gpt_send() {
  echo "$COMMAND" | grep -qE 'cdp_chat_send\.py|share-result|/finish'
}

if ! is_gpt_send; then
  exit 0
fi

INSTRUCTION_DIR="$PROJECT_ROOT/.claude/state/instruction_reads"

# 필수 읽기 마커 확인
ENTRY_OK="$INSTRUCTION_DIR/debate_entry_read.ok"
CLAUDE_OK="$INSTRUCTION_DIR/debate_claude_read.ok"

MISSING=""
if [ ! -f "$ENTRY_OK" ]; then
  MISSING="$MISSING\n  - 90_공통기준/토론모드/ENTRY.md"
fi
if [ ! -f "$CLAUDE_OK" ]; then
  MISSING="$MISSING\n  - 90_공통기준/토론모드/CLAUDE.md"
fi

if [ -n "$MISSING" ]; then
  MSG="[instruction_read_gate] GPT 전송 차단: 필수 지시문 미읽기.$(printf "$MISSING")\n\n먼저 위 파일을 Read/Grep으로 읽은 후 다시 시도하세요."
  hook_log "instruction_read_gate" "DENY missing=$(echo "$MISSING" | tr '\n' ',')"
  hook_incident "instruction_read_gate" "instruction_not_read" "GPT 전송 전 필수 지시문 미읽기: $MISSING"
  printf '{"hookSpecificOutput":{"permissionDecision":"deny"},"systemMessage":"%s"}' "$(echo -e "$MSG" | sed 's/"/\\"/g')" >&2
  exit 2
fi

hook_log "instruction_read_gate" "PASS entry+claude read confirmed"
exit 0
