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

# 공통 mtime 조회 (GNU/BSD stat 호환)
file_mtime() {
  local path="$1"
  if [ -z "$path" ] || [ ! -f "$path" ]; then
    echo 0
    return 0
  fi
  stat --format=%Y "$path" 2>/dev/null || stat -f %m "$path" 2>/dev/null || echo 0
}

# transcript에서 마지막 assistant text 추출
last_assistant_text() {
  local transcript="${1:-$CLAUDE_TRANSCRIPT_PATH}"
  if [ -z "$transcript" ] || [ ! -f "$transcript" ]; then
    return 1
  fi
  local last_assistant
  last_assistant=$(tail -n 120 "$transcript" 2>/dev/null | grep '"type":"assistant"' | tail -n 1)
  if [ -z "$last_assistant" ]; then
    return 1
  fi
  printf '%s' "$last_assistant" | safe_json_get "text"
}

# 운영 중 누적되지만 완료 판정에서 무시할 런타임 산출물
is_volatile_runtime_path() {
  local path="$1"
  echo "$path" | grep -qE '^(\.claude/(incident_ledger\.jsonl|settings\.local\.json|settings\.local\.json\.bak_[0-9]+|command-audit\.log|subagent-audit\.log|tool-failure\.log|logs/|state/)|90_공통기준/토론모드/logs/)'
}

# 사용자에게 완료/최종반영을 주장하는 표현만 좁게 감지
is_completion_claim() {
  local text="$1"
  if [ -z "$text" ]; then
    return 1
  fi
  echo "$text" | grep -qiE '(완료 보고|잔여 이슈|반영 완료|수정 완료|적용 완료|검증 완료|완료했습니다|완료됐습니다|ALL CLEAR|GPT 판정:[[:space:]]*PASS|커밋[[:space:]]+SHA|commit SHA|푸시 완료|pushed successfully)'
}

# Git 변경 중 런타임 산출물을 제외한 "실제 반영 대상"만 수집
git_relevant_change_list() {
  (
    cd "$PROJECT_ROOT" 2>/dev/null || exit 1
    {
      git -c core.quotepath=false diff --name-only 2>/dev/null
      git -c core.quotepath=false diff --cached --name-only 2>/dev/null
      git -c core.quotepath=false ls-files --others --exclude-standard 2>/dev/null
    } | sed '/^$/d' | sort -u
  ) | while IFS= read -r path; do
    if ! is_volatile_runtime_path "$path"; then
      printf '%s\n' "$path"
    fi
  done
}

git_has_relevant_changes() {
  local changes
  changes=$(git_relevant_change_list)
  [ -n "$changes" ]
}

hook_incident() {
  local type="$1"    # hook_block|compile_fail|gate_reject|encoding_error
  local hook="$2"    # 훅 이름
  local file="$3"    # 대상 파일 (없으면 "")
  local detail="$4"  # 상세 사유
  local extra_json="${5:-}"  # optional: '"key":"value"' 형태의 추가 필드
  local ts
  ts=$(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S')
  detail="${detail//\\/\\\\}"
  detail="${detail//\"/\\\"}"
  detail="${detail//$'\n'/\\n}"
  file="${file//\\/\\\\}"
  file="${file//\"/\\\"}"
  extra_json=$(printf '%s' "$extra_json" | tr -d '\n')
  echo "{\"ts\":\"$ts\",\"type\":\"$type\",\"hook\":\"$hook\",\"file\":\"$file\",\"detail\":\"$detail\",\"resolved\":false${extra_json:+,$extra_json}}" >> "$INCIDENT_LEDGER"
  _rotate_file "$INCIDENT_LEDGER"
}
