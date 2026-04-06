#!/bin/bash
# completion-gate v5: 순수 bash — python3 subprocess 제거 (#34457 Windows hooks 멈춤 대응)
# GPT+Claude 토론 합의 2026-04-06
source "$(dirname "$0")/hook_common.sh" 2>/dev/null
hook_log "Stop" "completion_gate v5" 2>/dev/null || true

STATE_DIR="${CLAUDE_PROJECT_DIR:-.}/90_공통기준/agent-control/state"
MARKER="$STATE_DIR/write_marker.flag"
TASKS="${CLAUDE_PROJECT_DIR:-.}/90_공통기준/업무관리/TASKS.md"
HANDOFF="${CLAUDE_PROJECT_DIR:-.}/90_공통기준/업무관리/HANDOFF.md"

# write_marker 없으면 skip
if [ ! -f "$MARKER" ]; then
  exit 0
fi

# marker timestamp (epoch seconds)
MARKER_EPOCH=$(stat --format=%Y "$MARKER" 2>/dev/null || stat -f %m "$MARKER" 2>/dev/null || echo 0)

MISSING=""
for NAME_PATH in "TASKS.md:$TASKS" "HANDOFF.md:$HANDOFF"; do
  NAME="${NAME_PATH%%:*}"
  FPATH="${NAME_PATH#*:}"
  if [ ! -f "$FPATH" ]; then
    MISSING="${MISSING}${MISSING:+,}$NAME"
    continue
  fi
  FILE_EPOCH=$(stat --format=%Y "$FPATH" 2>/dev/null || stat -f %m "$FPATH" 2>/dev/null || echo 0)
  if [ "$FILE_EPOCH" -lt "$MARKER_EPOCH" ] 2>/dev/null; then
    MISSING="${MISSING}${MISSING:+,}$NAME"
  fi
done

if [ -n "$MISSING" ]; then
  echo "{\"decision\":\"block\",\"reason\":\"[COMPLETION GATE] 파일 변경 후 ${MISSING} 미갱신 — 갱신 후 종료하세요.\"}"
else
  rm -f "$MARKER" 2>/dev/null
fi

exit 0
