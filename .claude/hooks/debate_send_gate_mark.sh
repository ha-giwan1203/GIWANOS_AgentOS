#!/bin/bash
# debate_send_gate_mark.sh — SEND GATE 마커 생성 (PostToolUse)
#
# 대상: mcp__Claude_in_Chrome__get_page_text
# 동작: ChatGPT 페이지에서 get_page_text 실행 시 debate_send_gate.ok 마커 생성
# 용도: debate_gate.sh가 이 마커를 확인하고 1회용으로 소비
#
# 세션46: 의지 기반 SEND GATE 실패 → hook 강제로 전환

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/hook_common.sh" 2>/dev/null || true
# 훅 등급: measurement (Phase 2-C 2026-04-19 세션73 timing 배선)
_DSG_MARK_START=$(hook_timing_start)

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
STATE_DIR="$PROJECT_DIR/.claude/state"

# tool_result에서 ChatGPT URL 확인
INPUT=$(cat)
RESULT_TEXT=$(echo "$INPUT" | safe_json_get "result" 2>/dev/null)

# ChatGPT 페이지인지 확인
if echo "$RESULT_TEXT" | grep -q 'chatgpt.com' 2>/dev/null; then
  mkdir -p "$STATE_DIR" 2>/dev/null
  date -u '+%Y-%m-%dT%H:%M:%SZ' > "$STATE_DIR/debate_send_gate.ok" 2>/dev/null
  hook_log "PostToolUse/debate_send_gate_mark" "SEND GATE 마커 생성" 2>/dev/null
  hook_timing_end "debate_send_gate_mark" "$_DSG_MARK_START" "marked"
else
  hook_timing_end "debate_send_gate_mark" "$_DSG_MARK_START" "skip"
fi

exit 0
