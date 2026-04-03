#!/bin/bash
# Subagent 시작/종료 Audit Log: SubagentStart/SubagentStop 이벤트 기록
# SubagentStart, SubagentStop 매처로 실행 (async: true)
# 합의: GPT+Claude 2026-04-01 영상분석 자동모드

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
LOG_FILE="$PROJECT_DIR/.claude/subagent-audit.log"
INPUT=$(cat)

EVENT=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('hook_event_name','unknown'))" 2>/dev/null)
AGENT_TYPE=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('agent_type','unknown'))" 2>/dev/null)
AGENT_ID=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('agent_id','unknown'))" 2>/dev/null)
TIMESTAMP=$(date '+%Y-%m-%dT%H:%M:%S')

# 로그 기록
echo "$TIMESTAMP | $EVENT | type=$AGENT_TYPE | id=$AGENT_ID" >> "$LOG_FILE"

# 로그 크기 제한 (2000줄 초과 시 최근 1000줄만 유지)
if [ -f "$LOG_FILE" ]; then
  LINE_COUNT=$(wc -l < "$LOG_FILE" 2>/dev/null)
  if [ "$LINE_COUNT" -gt 2000 ]; then
    tail -1000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
  fi
fi

exit 0
