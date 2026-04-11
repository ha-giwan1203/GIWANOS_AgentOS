#!/bin/bash
# PostToolUse 전용 — GPT 읽기/전송/후속작업 감지 → pending flag 관리
# gpt_followup_guard.sh에서 분리 (v2, 2026-04-06 GPT 합의)
# v3: python3→bash 전환 (#34457 Windows hooks 멈춤 대응)
source "$(dirname "$0")/hook_common.sh" 2>/dev/null || true

INPUT=$(cat)
# 안전 JSON 파서 사용 (sed 단독 파싱 취약성 대체, GPT+Claude 합의 2026-04-07)
TOOL_NAME=$(echo "$INPUT" | safe_json_get "tool_name")
TOOL_INPUT=$(echo "$INPUT" | safe_json_get "tool_input")

# C+ 합의(세션15): Stage 2 object 추출 실패 → fallback 사용 시 WARN 계측
if [ -n "$TOOL_NAME" ] && [ -z "$TOOL_INPUT" ]; then
  hook_log "PostToolUse/gpt_followup_post" "WARN: tool_input object 추출 실패 (tool=$TOOL_NAME), 문자열/빈값으로 진행" 2>/dev/null
fi

if [ -z "$TOOL_NAME" ]; then
  hook_log "PostToolUse/gpt_followup_post" "WARN: tool_name 파싱 실패 — skip" 2>/dev/null
  exit 0
fi

mkdir -p "$STATE_AGENT_CONTROL" 2>/dev/null
PENDING="$STATE_AGENT_CONTROL/gpt_followup_pending.flag"

TNAME_LOWER=$(echo "$TOOL_NAME" | tr '[:upper:]' '[:lower:]')

# GPT 응답 읽기 감지 → pending flag 생성
if echo "$TNAME_LOWER" | grep -q "javascript"; then
  if echo "$TOOL_INPUT" | grep -qiE '(data-message-author-role.*assistant|innertext|textcontent)'; then
    # 전송(send-button + .click 결합)이나 입력(execCommand + insertText 결합)은 읽기가 아님
    # GPT 피드백: send-button 문자열 단독 매칭은 읽기용 JS에서 오탐 (2026-04-07)
    if echo "$TOOL_INPUT" | grep -qiE '(send-button.*\.click|execCommand.*insertText)'; then
      rm -f "$PENDING" 2>/dev/null
      exit 0
    fi
    printf '{"event":"gpt_response_read","session_key":"%s","created_at":"%s"}\n' \
      "$(session_key 2>/dev/null || echo unknown)" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$PENDING"
    exit 0
  fi
fi

if echo "$TNAME_LOWER" | grep -qiE '(get_page_text|read_page)'; then
  printf '{"event":"gpt_response_read","session_key":"%s","created_at":"%s"}\n' \
    "$(session_key 2>/dev/null || echo unknown)" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$PENDING"
  exit 0
fi

# GPT 전송 감지 → pending flag 삭제
if echo "$TNAME_LOWER" | grep -q "javascript"; then
  if echo "$TOOL_INPUT" | grep -qiE '(send-button.*\.click|execCommand.*insertText|prompt-textarea.*execCommand)'; then
    rm -f "$PENDING" 2>/dev/null
    exit 0
  fi
fi

# 후속 작업 감지 → pending flag 삭제
case "$TOOL_NAME" in
  Bash|Edit|Write|MultiEdit)
    rm -f "$PENDING" 2>/dev/null
    ;;
  *)
    # Notion, Calendar, Gmail, Slack MCP도 후속 작업으로 인정
    if echo "$TNAME_LOWER" | grep -qiE '(notion|gcal|gmail|slack)'; then
      rm -f "$PENDING" 2>/dev/null
    fi
    ;;
esac
