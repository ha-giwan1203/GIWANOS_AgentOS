#!/bin/bash
# PreToolUse hook — MCP SEND GATE: Chrome MCP 입력 전 토론모드 SEND GATE 강제
#
# 대상: mcp__Claude_in_Chrome__form_input (ChatGPT 입력창에 텍스트 입력 시)
# 조건: 토론모드 활성 시에만 동작
# 검사: debate_claude_read.ok + debate_entry_read.ok 마커 존재 확인
#       (instruction_read_gate와 동일 기준 — 지침 미읽기 시 차단)
#
# CDP 폐기 후 Chrome MCP 단일화에 따른 전송 게이트 (2026-04-13)

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/hook_common.sh" 2>/dev/null || true

# 토론모드 활성 확인 — debate_preflight.req 존재 시에만 동작
SESSION_KEY="$(session_key 2>/dev/null || echo '')"
SESSION_DIR="$STATE_EVIDENCE/$SESSION_KEY"
REQ_FILE="$SESSION_DIR/requires/debate_preflight.req"

if [ ! -f "$REQ_FILE" ] 2>/dev/null; then
  # 토론 도메인이 아니면 무조건 통과
  exit 0
fi

# 필수 읽기 마커 확인 (instruction_read_gate와 동일 기준)
INSTRUCTION_DIR="$PROJECT_ROOT/.claude/state/instruction_reads"
ENTRY_OK="$INSTRUCTION_DIR/debate_entry_read.ok"
CLAUDE_OK="$INSTRUCTION_DIR/debate_claude_read.ok"

MISSING=""
if [ ! -f "$ENTRY_OK" ]; then
  MISSING="$MISSING ENTRY.md"
fi
if [ ! -f "$CLAUDE_OK" ]; then
  MISSING="$MISSING CLAUDE.md"
fi

if [ -n "$MISSING" ]; then
  hook_log "PreToolUse/mcp_send_gate" "BLOCK: 토론모드 지침 미읽기 —$MISSING" 2>/dev/null
  echo "{\"decision\":\"deny\",\"reason\":\"[MCP SEND GATE] 토론모드 지침 미읽기:${MISSING}. 먼저 토론모드 ENTRY.md와 CLAUDE.md를 읽은 후 다시 시도하세요.\"}"
  exit 0
fi

hook_log "PreToolUse/mcp_send_gate" "PASS: 토론모드 지침 읽기 확인됨" 2>/dev/null
exit 0
