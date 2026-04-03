#!/bin/bash
# PostToolUseFailure: 도구 실패 시 로그 기록 + 알림
# 조용한 실패 방지 — 모든 도구 실패를 기록
# 합의: GPT+Claude 2026-04-01

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
LOG_FILE="$PROJECT_DIR/.claude/tool-failure.log"
INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name','unknown'))" 2>/dev/null)
ERROR_MSG=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error','no error message')[:200])" 2>/dev/null)
TIMESTAMP=$(date '+%Y-%m-%dT%H:%M:%S')

# 로그 기록
echo "$TIMESTAMP | FAIL | $TOOL_NAME | $ERROR_MSG" >> "$LOG_FILE"

# 로그 파일 크기 제한 (1000줄 초과 시 최근 500줄만 유지)
if [ -f "$LOG_FILE" ]; then
  LINE_COUNT=$(wc -l < "$LOG_FILE")
  if [ "$LINE_COUNT" -gt 1000 ]; then
    tail -500 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
  fi
fi

echo "{\"message\":\"[TOOL FAIL] $TOOL_NAME 실패 — $ERROR_MSG (tool-failure.log 기록됨)\"}"
exit 0
