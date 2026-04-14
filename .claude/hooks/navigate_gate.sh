#!/bin/bash
# navigate_gate.sh — ChatGPT 진입 시 토론모드 지침 읽기 강제 (PreToolUse)
#
# 대상: mcp__Claude_in_Chrome__navigate
# 조건: chatgpt.com URL + 토론 도메인 활성 상태
# 차단: 토론모드 CLAUDE.md 미읽기 시 deny
#
# 세션47: 토론방 입장 시 지침 미읽기 + 스킬 미사용 반복 → 훅 강제

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/hook_common.sh" 2>/dev/null || true

INPUT=$(cat)
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
STATE_DIR="$PROJECT_DIR/.claude/state"

# URL 추출
URL=$(echo "$INPUT" | safe_json_get "tool_input.url" 2>/dev/null)
[ -z "$URL" ] && URL=$(echo "$INPUT" | safe_json_get "url" 2>/dev/null)

# chatgpt.com이 아니면 통과
if ! echo "$URL" | grep -qi 'chatgpt\.com' 2>/dev/null; then
  exit 0
fi

# 토론 도메인 활성 여부 확인
DOMAIN_REQ="$STATE_DIR/active_domain.req"
if [ ! -f "$DOMAIN_REQ" ]; then
  exit 0
fi

ACTIVE_DOMAIN=$(grep '^domain_id=' "$DOMAIN_REQ" 2>/dev/null | cut -d= -f2)
if [ "$ACTIVE_DOMAIN" != "debate_mode" ]; then
  exit 0
fi

# === 토론 도메인 + ChatGPT 진입 시도 ===

# 토론모드 CLAUDE.md 읽기 마커 확인
INSTRUCTION_DIR="$STATE_DIR/instruction_reads"
CLAUDE_OK="$INSTRUCTION_DIR/debate_claude_read.ok"

if [ ! -f "$CLAUDE_OK" ]; then
  hook_log "PreToolUse/navigate_gate" "DENY: 토론모드 CLAUDE.md 미읽기 — URL=$URL"
  hook_incident "navigate_gate" "gate_reject" "토론모드 ChatGPT 진입 차단: CLAUDE.md 미읽기" '"classification_reason":"instruction_not_read"'
  echo "{\"decision\":\"deny\",\"reason\":\"[NAVIGATE GATE] 토론모드 CLAUDE.md를 먼저 읽으세요.\\n\\n토론 도메인 활성 상태에서 ChatGPT 진입 시:\\n1. Read 90_공통기준/토론모드/CLAUDE.md\\n2. debate-mode 스킬 사용 (/debate-mode 또는 Skill 도구)\\n\\n수동 navigate 대신 debate-mode 스킬이 절차를 자동 처리합니다.\"}"
  exit 0
fi

hook_log "PreToolUse/navigate_gate" "PASS: CLAUDE.md 읽기 확인 — URL=$URL"
exit 0
