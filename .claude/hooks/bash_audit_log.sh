#!/bin/bash
# Bash 명령 Audit Log: 모든 Bash 실행을 기록
# PostToolUse(Bash) 매처로 실행
# 합의: GPT+Claude 2026-04-01

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
LOG_FILE="$PROJECT_DIR/.claude/command-audit.log"
INPUT=$(cat)

CMD=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command','unknown')[:300])" 2>/dev/null)
TIMESTAMP=$(date '+%Y-%m-%dT%H:%M:%S')

# 로그 기록
echo "$TIMESTAMP | $CMD" >> "$LOG_FILE"

# 로그 크기 제한 (2000줄 초과 시 최근 1000줄만 유지)
if [ -f "$LOG_FILE" ]; then
  LINE_COUNT=$(wc -l < "$LOG_FILE" 2>/dev/null)
  if [ "$LINE_COUNT" -gt 2000 ]; then
    tail -1000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
  fi
fi

exit 0
