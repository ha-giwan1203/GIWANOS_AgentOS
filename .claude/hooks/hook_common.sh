#!/bin/bash
# 훅 공통 로깅 함수 + 로그 로테이션
# 사용법: source .claude/hooks/hook_common.sh && hook_log "이벤트명" "메시지"

HOOK_LOG_FILE="${CLAUDE_PROJECT_DIR:-.}/.claude/hooks/hook_log.txt"
HOOK_LOG_MAX_SIZE=512000  # 500KB

hook_log() {
  local event="$1"
  local msg="$2"
  local ts
  ts=$(date '+%Y-%m-%d %H:%M:%S')
  echo "[Hook] $event: $msg ($ts)" >> "$HOOK_LOG_FILE"

  # 로테이션: 500KB 초과 시 최근 2000줄만 유지
  if [ -f "$HOOK_LOG_FILE" ]; then
    local size
    size=$(wc -c < "$HOOK_LOG_FILE" 2>/dev/null || echo 0)
    if [ "$size" -gt "$HOOK_LOG_MAX_SIZE" ] 2>/dev/null; then
      local tmp="${HOOK_LOG_FILE}.tmp"
      tail -n 2000 "$HOOK_LOG_FILE" > "$tmp" 2>/dev/null && mv "$tmp" "$HOOK_LOG_FILE" 2>/dev/null
    fi
  fi
}
