#!/bin/bash
# 훅 공통 로깅 함수
# 사용법: source .claude/hooks/hook_common.sh && hook_log "이벤트명" "메시지"

HOOK_LOG_FILE="${CLAUDE_PROJECT_DIR:-.}/.claude/hooks/hook_log.txt"

hook_log() {
  local event="$1"
  local msg="$2"
  local ts
  ts=$(date '+%Y-%m-%d %H:%M:%S')
  echo "[Hook] $event: $msg ($ts)" >> "$HOOK_LOG_FILE"
}
