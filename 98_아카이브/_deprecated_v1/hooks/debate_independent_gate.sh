#!/bin/bash
# debate_independent_gate.sh — 독립 의견 없이 GPT/Gemini 응답 전달 차단 (PreToolUse)
#
# 대상:
#   - mcp__Claude_in_Chrome__javascript_tool (구 MCP, 세션46)
#   - mcp__chrome-devtools-mcp__evaluate_script (세션105 전환)
# 조건: ChatGPT prompt-textarea 또는 Gemini ql-editor에 insertText 시 + 토론모드 활성
#
# 강제 규칙:
# GPT/Gemini 응답을 읽은 뒤 Claude가 독립 분석을 먼저 수행했는지 확인.
# debate_independent_review.ok 마커가 없으면 전송 차단.
#
# 마커 생성 조건: Claude가 응답에 대해 하네스 분석(채택/보류/버림)을
# 사용자에게 보고한 후 수동으로 찍어야 함 → 이 hook이 1회용으로 소비.
#
# 세션46: GPT 프레임 종속 반복 → hook 강제로 전환
# 세션105 2026-04-25: chrome-devtools-mcp evaluate_script 매처 확장 + Gemini ql-editor 셀렉터 병행 (사용자 지시 예외 적용)

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/hook_common.sh" 2>/dev/null || true
# 훅 등급: gate (Phase 2-C 2026-04-19 세션73 timing 배선, exit 2 승격은 1주 수집 후)
_DIG_START=$(hook_timing_start)

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
STATE_DIR="$PROJECT_DIR/.claude/state"

# 도구 이름별 payload 필드 분기 (세션105 chrome-devtools-mcp 전환 대응)
TOOL_NAME=$(echo "$INPUT" | safe_json_get "tool_name" 2>/dev/null)

# 신/구 MCP 모두 커버 — 전체 tool_input JSON을 payload로 간주
TEXT_CONTENT=$(echo "$INPUT" | safe_json_get "tool_input" 2>/dev/null)
[ -z "$TEXT_CONTENT" ] && TEXT_CONTENT=$(echo "$INPUT" | safe_json_get "input" 2>/dev/null)

# insertText 포함이 아니면 skip (전송이 아닌 일반 평가/읽기 스크립트는 제외)
if ! echo "$TEXT_CONTENT" | grep -q 'insertText' 2>/dev/null; then
  hook_timing_end "debate_independent_gate" "$_DIG_START" "skip_noninsert"
  exit 0
fi
# ChatGPT prompt-textarea 또는 Gemini ql-editor 중 하나라도 포함되면 전송으로 간주
if ! echo "$TEXT_CONTENT" | grep -qE 'prompt-textarea|ql-editor' 2>/dev/null; then
  hook_timing_end "debate_independent_gate" "$_DIG_START" "skip_nontextarea"
  exit 0
fi

# 독립 의견 마커 확인
REVIEW_MARKER="$STATE_DIR/debate_independent_review.ok"
if [ ! -f "$REVIEW_MARKER" ] 2>/dev/null; then
  hook_log "PreToolUse/debate_independent_gate" "BLOCK: 독립 의견 미수행 — GPT 응답에 대한 하네스 분석을 먼저 사용자에게 보고하세요" 2>/dev/null
  echo "{\"hookSpecificOutput\":{\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"[DEBATE INDEPENDENT GATE] GPT 응답에 대한 독립 의견을 먼저 사용자에게 보고하세요.\\n\\n1. GPT 응답 주장 분해 (2~4개)\\n2. 라벨링 (실증됨/일반론/환경미스매치/과잉설계)\\n3. 채택/보류/버림 판정\\n4. 사용자 보고 후 전송 진행\\n\\n하네스 분석 없이 GPT에 바로 답장할 수 없습니다.\"}}"
  hook_timing_end "debate_independent_gate" "$_DIG_START" "block_missing"
  exit 0
fi

# 마커 1회용 소비
rm -f "$REVIEW_MARKER" 2>/dev/null
hook_log "PreToolUse/debate_independent_gate" "PASS: 독립 의견 확인됨" 2>/dev/null
hook_timing_end "debate_independent_gate" "$_DIG_START" "pass"
exit 0
