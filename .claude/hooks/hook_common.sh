#!/bin/bash
# 훅 공통 로깅 함수 + 로그 로테이션 + incident 기록
# 사용법: source .claude/hooks/hook_common.sh && hook_log "이벤트명" "메시지"
# incident: hook_incident "type" "hook" "file" "detail"

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-.}"
HOOK_LOG_FILE="$PROJECT_ROOT/.claude/hooks/hook_log.jsonl"
HOOK_LOG_MAX_SIZE=512000  # 500KB
INCIDENT_LEDGER="$PROJECT_ROOT/.claude/incident_ledger.jsonl"

# 공통 경로 — 개별 훅에서 하드코딩 대신 이 변수 사용
STATE_EVIDENCE="$PROJECT_ROOT/.claude/state/evidence"
STATE_AGENT_CONTROL="$PROJECT_ROOT/90_공통기준/agent-control/state"
PATH_TASKS="$PROJECT_ROOT/90_공통기준/업무관리/TASKS.md"
PATH_HANDOFF="$PROJECT_ROOT/90_공통기준/업무관리/HANDOFF.md"

# 세션 키 — evidence 시스템의 세션 격리용 (sha1 of transcript path)
session_key() {
  local seed="${CLAUDE_TRANSCRIPT_PATH:-$PWD}"
  if command -v sha1sum >/dev/null 2>&1; then
    printf '%s' "$seed" | sha1sum | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    printf '%s' "$seed" | shasum | awk '{print $1}'
  else
    printf '%s' "$seed" | cksum | awk '{print $1}'
  fi
}

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

# 스킬 사용 로깅 — 스킬 호출 시 전용 계측
# 사용법: hook_skill_usage "skill_name" "trigger_type"
SKILL_USAGE_LOG="$PROJECT_ROOT/.claude/hooks/skill_usage.jsonl"

hook_skill_usage() {
  local skill_name="$1"
  local trigger_type="${2:-manual}"  # manual|slash|auto
  local ts
  ts=$(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S')
  local sk
  sk=$(session_key)
  skill_name="${skill_name//\\/\\\\}"
  skill_name="${skill_name//\"/\\\"}"
  echo "{\"ts\":\"$ts\",\"skill\":\"$skill_name\",\"trigger\":\"$trigger_type\",\"session\":\"$sk\"}" >> "$SKILL_USAGE_LOG"
  _rotate_file "$SKILL_USAGE_LOG"
}

# 안전 JSON 값 추출 — sed 단독 파싱의 따옴표/줄바꿈 취약성 대체
# 사용법: VALUE=$(echo "$JSON" | safe_json_get "key_name")
# 문자열 값: 따옴표 내부를 이스케이프 인식하며 추출
# 객체 값: 중괄호 매칭으로 추출
safe_json_get() {
  local key="$1"
  local input
  input=$(cat)
  # 1차: 문자열 값 — 이스케이프된 따옴표(\")를 건너뛰며 추출
  local val
  val=$(printf '%s' "$input" | tr '\n' ' ' | sed -n 's/.*"'"$key"'"[[:space:]]*:[[:space:]]*"\(\([^"\\]\|\\.\)*\)".*/\1/p' | head -1)
  if [ -n "$val" ]; then
    # 이스케이프 복원: \" → ", \\ → \, \n → 개행, \t → 탭
    val=$(printf '%s' "$val" | sed 's/\\"/"/g; s/\\n/\n/g; s/\\t/\t/g; s/\\\\/\\/g')
    printf '%s' "$val"
    return 0
  fi
  # 2차: 객체/배열 값 — 첫 번째 { 또는 [ 부터 매칭
  val=$(printf '%s' "$input" | tr '\n' ' ' | sed -n 's/.*"'"$key"'"[[:space:]]*:[[:space:]]*\(\({[^}]*}\)\|\(\[.*\]\)\).*/\1/p' | head -1)
  if [ -n "$val" ]; then
    printf '%s' "$val"
    return 0
  fi
  return 1
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
