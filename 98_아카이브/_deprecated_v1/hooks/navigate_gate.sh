#!/bin/bash
# navigate_gate.sh — ChatGPT 진입 시 토론모드 지침 읽기 강제 (PreToolUse)
#
# 대상:
#   - mcp__Claude_in_Chrome__navigate (구 MCP, 세션47)
#   - mcp__chrome-devtools-mcp__navigate_page (세션105 Q4 3자 합의)
#   - mcp__chrome-devtools-mcp__new_page (세션105 Q4 3자 합의)
# 조건: chatgpt.com URL → 도메인 활성 여부 무관하게 CLAUDE.md 읽기 강제
# 차단: 토론모드 CLAUDE.md 미읽기 시 deny
#
# 세션47: 토론방 입장 시 지침 미읽기 + 스킬 미사용 반복 → 훅 강제
# 세션51: 도메인 활성 조건 제거 — gpt-send 직접 호출 시에도 게이트 적용
# 세션105 Q4: chrome-devtools-mcp 전환 후 신규 MCP 매처 확장 (navigate_page, new_page)
#   - select_page, evaluate_script, take_snapshot, click, fill은 URL 진입 아니므로 제외
#   - navigate_page는 type="url"일 때만 검사 (reload/back/forward 제외)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/hook_common.sh" 2>/dev/null || true
# 훅 등급: gate (Phase 2-C 2026-04-19 세션73 timing 배선, exit 2 승격은 1주 수집 후)
_NG_START=$(hook_timing_start)

INPUT=$(cat)
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
STATE_DIR="$PROJECT_DIR/.claude/state"

# 도구 이름 추출 (세션105 Q4 — navigate_page type 분기용)
TOOL_NAME=$(echo "$INPUT" | safe_json_get "tool_name" 2>/dev/null)

# URL 추출 (공통 필드)
URL=$(echo "$INPUT" | safe_json_get "tool_input.url" 2>/dev/null)
[ -z "$URL" ] && URL=$(echo "$INPUT" | safe_json_get "url" 2>/dev/null)

# navigate_page는 type="url"일 때만 URL 진입으로 간주 (세션105 Q4 3자 합의)
if [ "$TOOL_NAME" = "mcp__chrome-devtools-mcp__navigate_page" ]; then
  NAV_TYPE=$(echo "$INPUT" | safe_json_get "tool_input.type" 2>/dev/null)
  if [ -n "$NAV_TYPE" ] && [ "$NAV_TYPE" != "url" ]; then
    hook_timing_end "navigate_gate" "$_NG_START" "skip_navtype_$NAV_TYPE"
    exit 0
  fi
fi

# chatgpt.com이 아니면 통과
if ! echo "$URL" | grep -qi 'chatgpt\.com' 2>/dev/null; then
  hook_timing_end "navigate_gate" "$_NG_START" "skip_nonchatgpt"
  exit 0
fi

# === ChatGPT 진입 시도 — 도메인 활성 여부 무관 ===

# 토론모드 CLAUDE.md 읽기 마커 확인
INSTRUCTION_DIR="$STATE_DIR/instruction_reads"
CLAUDE_OK="$INSTRUCTION_DIR/debate_claude_read.ok"

if [ ! -f "$CLAUDE_OK" ]; then
  hook_log "PreToolUse/navigate_gate" "DENY: 토론모드 CLAUDE.md 미읽기 — URL=$URL"
  hook_incident "gate_reject" "navigate_gate" "" "ChatGPT 진입 차단: 토론모드 CLAUDE.md 미읽기" '"classification_reason":"send_block"'
  echo "{\"hookSpecificOutput\":{\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"[NAVIGATE GATE] 토론모드 CLAUDE.md를 먼저 읽으세요.\\n\\nChatGPT 진입 전 필수:\\n1. Read 90_공통기준/토론모드/CLAUDE.md\\n2. debate-mode 또는 gpt-send 스킬 사용\\n\\n지침 미읽기 상태에서는 ChatGPT navigate가 차단됩니다.\"}}"
  hook_timing_end "navigate_gate" "$_NG_START" "block_missing"
  exit 0
fi

hook_log "PreToolUse/navigate_gate" "PASS: CLAUDE.md 읽기 확인 — URL=$URL"
hook_timing_end "navigate_gate" "$_NG_START" "pass"
exit 0
