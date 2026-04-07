#!/bin/bash
# PostToolUse 전용 — GPT 읽기/전송/후속작업 감지 → pending flag 관리
# gpt_followup_guard.sh에서 분리 (v2, 2026-04-06 GPT 합의)
# v3: python3→bash 전환 (#34457 Windows hooks 멈춤 대응)
source "$(dirname "$0")/hook_common.sh" 2>/dev/null || true

INPUT=$(cat)
# bash-only JSON 파싱 (python3 의존 제거)
TOOL_NAME=$(echo "$INPUT" | sed -n 's/.*"tool_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
TOOL_INPUT=$(echo "$INPUT" | sed -n 's/.*"tool_input"[[:space:]]*:[[:space:]]*\({.*}\).*/\1/p' | head -1)

mkdir -p "$STATE_AGENT" 2>/dev/null
PENDING="$STATE_AGENT/gpt_followup_pending.flag"

TNAME_LOWER=$(echo "$TOOL_NAME" | tr '[:upper:]' '[:lower:]')

# GPT 응답 읽기 감지 → pending flag 생성
if echo "$TNAME_LOWER" | grep -q "javascript"; then
  if echo "$TOOL_INPUT" | grep -qiE '(data-message-author-role.*assistant|innertext|textcontent)'; then
    # 전송(send-button click)이나 입력(insertText)은 읽기가 아님
    if echo "$TOOL_INPUT" | grep -qiE '(send-button.*click|inserttext)'; then
      rm -f "$PENDING" 2>/dev/null
      exit 0
    fi
    echo "gpt_response_read" > "$PENDING"
    exit 0
  fi
fi

if echo "$TNAME_LOWER" | grep -qiE '(get_page_text|read_page)'; then
  echo "gpt_response_read" > "$PENDING"
  exit 0
fi

# GPT 전송 감지 → pending flag 삭제
if echo "$TNAME_LOWER" | grep -q "javascript"; then
  if echo "$TOOL_INPUT" | grep -qiE '(send-button|prompt-textarea|execcommand.*inserttext)'; then
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
