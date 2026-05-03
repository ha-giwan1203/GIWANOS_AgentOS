#!/bin/bash
# debate_gate.sh — 토론모드 전체 절차 강제 (PreToolUse)
#
# 대상: mcp__Claude_in_Chrome__javascript_tool (insertText 포함 시)
# 조건: ChatGPT 탭에서 insertText 실행 시에만 동작
#
# 강제 체크리스트 (세션46 사용자 요청):
# 1. 토론모드 지침(CLAUDE.md) 읽기 완료
# 2. 채팅방 진입 완료 (debate_chat_url 현재 세션 갱신)
# 3. SEND GATE — 전송 직전 get_page_text 실행 완료 (.ok 마커)
#
# 의지 기반 교정이 반복 실패하여 hook 강제로 전환 (세션46)

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/hook_common.sh" 2>/dev/null || true
# 훅 등급: gate (Phase 2-C 2026-04-19 세션73 timing 배선, exit 2 승격은 1주 수집 후)
_DBG_START=$(hook_timing_start)

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
STATE_DIR="$PROJECT_DIR/.claude/state"

# insertText가 포함된 호출인지 확인 — 아니면 통과
TEXT_CONTENT=$(echo "$INPUT" | safe_json_get "input" 2>/dev/null)
if ! echo "$TEXT_CONTENT" | grep -q 'insertText' 2>/dev/null; then
  hook_timing_end "debate_gate" "$_DBG_START" "skip_noninsert"
  exit 0
fi

# ChatGPT 대상인지 확인 — tabId로는 판단 어려우므로 insertText + prompt-textarea 조합으로 판단
if ! echo "$TEXT_CONTENT" | grep -q 'prompt-textarea' 2>/dev/null; then
  hook_timing_end "debate_gate" "$_DBG_START" "skip_nontextarea"
  exit 0
fi

# === 여기서부터 토론모드 전송으로 간주 ===

MISSING=""

# 1. 토론모드 지침 읽기 확인
INSTRUCTION_DIR="$STATE_DIR/instruction_reads"
if [ ! -f "$INSTRUCTION_DIR/debate_claude_read.ok" ] 2>/dev/null; then
  MISSING="$MISSING [토론모드 CLAUDE.md 미읽기]"
fi

# 2. 채팅방 진입 확인 (debate_chat_url이 현재 세션에서 갱신됐는지)
CHAT_URL_FILE="$STATE_DIR/debate_chat_url"
if [ ! -f "$CHAT_URL_FILE" ] 2>/dev/null; then
  MISSING="$MISSING [채팅방 URL 미설정]"
fi

# 3. SEND GATE — 전송 직전 대화창 읽기 마커 확인
SEND_GATE_MARKER="$STATE_DIR/debate_send_gate.ok"
if [ ! -f "$SEND_GATE_MARKER" ] 2>/dev/null; then
  MISSING="$MISSING [SEND GATE: 전송 전 get_page_text 미실행]"
else
  # 마커가 있으면 사용 후 삭제 (1회용 — 매 전송마다 새로 찍어야 함)
  rm -f "$SEND_GATE_MARKER" 2>/dev/null
fi

if [ -n "$MISSING" ]; then
  hook_log "PreToolUse/debate_gate" "BLOCK: 토론모드 절차 미완료 —$MISSING" 2>/dev/null
  echo "{\"hookSpecificOutput\":{\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"[DEBATE GATE] 토론모드 전송 절차 미완료:\\n$MISSING\\n\\n전송 전에 반드시:\\n1. 토론모드 CLAUDE.md 읽기\\n2. 채팅방 진입 + URL 갱신\\n3. get_page_text로 현재 대화 상태 확인 (SEND GATE)\\n을 완료하세요.\"}}"
  hook_timing_end "debate_gate" "$_DBG_START" "block_missing"
  exit 0
fi

hook_log "PreToolUse/debate_gate" "PASS: 토론모드 전체 절차 확인됨" 2>/dev/null
hook_timing_end "debate_gate" "$_DBG_START" "pass"
exit 0
