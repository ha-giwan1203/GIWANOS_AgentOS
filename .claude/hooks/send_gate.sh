#!/bin/bash
# PreToolUse hook — SEND GATE: ChatGPT 직접 전송 예비 경로 차단
# CDP 단일화(2026-04-11 GPT 합의): 기본 전송은 cdp_chat_send.py가 자체 검증.
# 이 hook은 직접 JS 예비 경로(javascript_tool + execCommand)를 deprecated 차단한다.
# 대상: mcp__Claude_in_Chrome__javascript_tool 호출 중 execCommand('insertText') 포함 시
# 조건: 토론모드 활성 시 직접 JS 전송을 차단하고 CDP 기본 경로 사용을 강제

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/hook_common.sh" 2>/dev/null || true

json_value() {
  local payload="$1"
  local key="$2"
  if type safe_json_get >/dev/null 2>&1; then
    printf '%s' "$payload" | safe_json_get "$key" 2>/dev/null || true
  fi
}

# hook_common safe_json_get 우선, 실패 시 기존 추출 fallback
TOOL_NAME=$(json_value "$INPUT" "tool_name")
if [ -z "$TOOL_NAME" ]; then
  TOOL_NAME=$(echo "$INPUT" | sed -n 's/.*"tool_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
fi

# javascript_tool 예비 경로가 아니면 통과 (기본 경로 cdp_chat_send.py는 자체 검증)
if [[ "$TOOL_NAME" != *"javascript_tool"* ]]; then
  exit 0
fi

# 가능하면 실제 tool_input/code 범위만 검사하고, 실패 시 원문 전체 fallback
TOOL_INPUT=$(json_value "$INPUT" "tool_input")
TOOL_CODE=$(json_value "$TOOL_INPUT" "code")
TOOL_TEXT=$(json_value "$TOOL_INPUT" "text")

INSPECT_SOURCE="$INPUT"
if [ -n "$TOOL_INPUT" ]; then
  INSPECT_SOURCE="$TOOL_INPUT"
fi
if [ -n "$TOOL_CODE" ]; then
  INSPECT_SOURCE="$TOOL_CODE"
fi

QUALITY_SOURCE="$INSPECT_SOURCE"
if [ -n "$TOOL_TEXT" ]; then
  QUALITY_SOURCE="$TOOL_TEXT"
fi

# text 파라미터에 execCommand + insertText 패턴 확인
HAS_INSERT="NO"
if echo "$INSPECT_SOURCE" | grep -q 'execCommand' && echo "$INSPECT_SOURCE" | grep -q 'insertText'; then
  HAS_INSERT="YES"
fi

# insertText가 아니면 통과 (일반 JS 실행은 차단하지 않음)
if [[ "$HAS_INSERT" != "YES" ]]; then
  exit 0
fi

# debate 도메인 활성 확인 — 토론모드가 아니면 통과
DEBATE_FLAG="${TEMP:-/tmp}/.claude_domain_debate_active"
if [ -f "$DEBATE_FLAG" ]; then
  ACTIVE_DOMAIN=$(cat "$DEBATE_FLAG" 2>/dev/null)
  # 매칭 완화 (세션 11): exact → contains. "debate" 문자열 포함 시 활성 판정
  if [[ "$ACTIVE_DOMAIN" != *"debate"* ]]; then
    exit 0
  fi
else
  exit 0
fi

# CDP 단일화: 토론모드에서 직접 JS 전송(예비 경로)은 deprecated → 차단
# 기본 전송 경로인 cdp_chat_send.py(Bash 호출)는 자체 검증 처리
hook_log "PreToolUse/send_gate" "BLOCK: deprecated_direct_js_send | 토론모드에서 직접 JS 전송 차단, cdp_chat_send.py 사용 필수" 2>/dev/null
hook_incident "hook_block" "send_gate" "" "deprecated: 직접 JS 전송. CDP 기본 경로(cdp_chat_send.py) 사용 필수" '"classification_reason":"send_block"' 2>/dev/null || true
echo '{"decision":"block","reason":"[CDP 단일화] 토론모드에서 직접 JS 전송(execCommand+insertText)은 deprecated되었습니다. cdp_chat_send.py를 사용하세요: python .claude/scripts/cdp/cdp_chat_send.py --match-url <url> --text-file <file> --require-korean --mark-send-gate"}'
exit 0
