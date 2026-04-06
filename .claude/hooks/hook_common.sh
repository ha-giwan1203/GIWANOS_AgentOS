#!/bin/bash
# 훅 공통 로깅 함수 + 로그 로테이션 + incident 기록
# 사용법: source .claude/hooks/hook_common.sh && hook_log "이벤트명" "메시지"
# incident: hook_incident "type" "hook" "file" "detail"

HOOK_LOG_FILE="${CLAUDE_PROJECT_DIR:-.}/.claude/hooks/hook_log.jsonl"
HOOK_LOG_MAX_SIZE=512000  # 500KB
INCIDENT_LEDGER="${CLAUDE_PROJECT_DIR:-.}/.claude/incident_ledger.jsonl"

_rotate_file() {
  local f="$1"
  if [ -f "$f" ]; then
    local size
    size=$(wc -c < "$f" 2>/dev/null || echo 0)
    if [ "$size" -gt "$HOOK_LOG_MAX_SIZE" ] 2>/dev/null; then
      local tmp="${f}.tmp"
      tail -n 2000 "$f" > "$tmp" 2>/dev/null && mv "$tmp" "$f" 2>/dev/null
    fi
  fi
}

hook_log() {
  local event="$1"
  local msg="$2"
  local ts
  ts=$(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S')
  # JSON 안전 이스케이프: 쌍따옴표, 백슬래시, 개행
  msg="${msg//\\/\\\\}"
  msg="${msg//\"/\\\"}"
  msg="${msg//$'\n'/\\n}"
  echo "{\"ts\":\"$ts\",\"event\":\"$event\",\"msg\":\"$msg\"}" >> "$HOOK_LOG_FILE"
  _rotate_file "$HOOK_LOG_FILE"
}

hook_incident() {
  local type="$1"    # hook_block|compile_fail|gate_reject|encoding_error
  local hook="$2"    # 훅 이름
  local file="$3"    # 대상 파일 (없으면 "")
  local detail="$4"  # 상세 사유
  local ts
  ts=$(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S')
  detail="${detail//\\/\\\\}"
  detail="${detail//\"/\\\"}"
  detail="${detail//$'\n'/\\n}"
  file="${file//\\/\\\\}"
  file="${file//\"/\\\"}"
  echo "{\"ts\":\"$ts\",\"type\":\"$type\",\"hook\":\"$hook\",\"file\":\"$file\",\"detail\":\"$detail\",\"resolved\":false}" >> "$INCIDENT_LEDGER"
  _rotate_file "$INCIDENT_LEDGER"
}
