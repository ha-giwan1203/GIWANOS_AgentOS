#!/bin/bash
# debate_independent_gate.sh — 독립 의견 없이 GPT 응답 전달 차단 (PreToolUse)
#
# 대상: mcp__Claude_in_Chrome__javascript_tool (insertText 포함 시)
# 조건: ChatGPT prompt-textarea에 insertText 시 + 토론모드 활성
#
# 강제 규칙:
# GPT 응답을 읽은 뒤(get_page_text) Claude가 독립 분석을 먼저 수행했는지 확인.
# debate_independent_review.ok 마커가 없으면 전송 차단.
#
# 마커 생성 조건: Claude가 GPT 응답에 대해 하네스 분석(채택/보류/버림)을
# 사용자에게 보고한 후 수동으로 찍어야 함 → 이 hook이 1회용으로 소비.
#
# 세션46: GPT 프레임 종속 반복 → hook 강제로 전환

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/hook_common.sh" 2>/dev/null || true

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
STATE_DIR="$PROJECT_DIR/.claude/state"

# insertText + prompt-textarea 조합만 대상
TEXT_CONTENT=$(echo "$INPUT" | safe_json_get "input" 2>/dev/null)
if ! echo "$TEXT_CONTENT" | grep -q 'insertText' 2>/dev/null; then
  exit 0
fi
if ! echo "$TEXT_CONTENT" | grep -q 'prompt-textarea' 2>/dev/null; then
  exit 0
fi

# 독립 의견 마커 확인
REVIEW_MARKER="$STATE_DIR/debate_independent_review.ok"
if [ ! -f "$REVIEW_MARKER" ] 2>/dev/null; then
  hook_log "PreToolUse/debate_independent_gate" "BLOCK: 독립 의견 미수행 — GPT 응답에 대한 하네스 분석을 먼저 사용자에게 보고하세요" 2>/dev/null
  echo "{\"hookSpecificOutput\":{\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"[DEBATE INDEPENDENT GATE] GPT 응답에 대한 독립 의견을 먼저 사용자에게 보고하세요.\\n\\n1. GPT 응답 주장 분해 (2~4개)\\n2. 라벨링 (실증됨/일반론/환경미스매치/과잉설계)\\n3. 채택/보류/버림 판정\\n4. 사용자 보고 후 전송 진행\\n\\n하네스 분석 없이 GPT에 바로 답장할 수 없습니다.\"}}"
  exit 0
fi

# 마커 1회용 소비
rm -f "$REVIEW_MARKER" 2>/dev/null
hook_log "PreToolUse/debate_independent_gate" "PASS: 독립 의견 확인됨" 2>/dev/null
exit 0
