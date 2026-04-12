#!/bin/bash
# 훅 공통 로깅 함수 + 로그 로테이션 + incident 기록
# 사용법: source .claude/hooks/hook_common.sh && hook_log "이벤트명" "메시지"
# incident: hook_incident "type" "hook" "file" "detail" ['"classification_reason":"<enum>"']
# type: gate_reject | hook_block | compile_fail
# classification_reason enum (세션12 합의):
#   evidence_missing | completion_false_positive | pre_commit_fail |
#   scope_violation | dangerous_cmd | send_block | stop_guard_block |
#   compile_fail | completion_before_git | completion_before_state_sync

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
# 원시 값: true/false/null/숫자 추출 (세션14 추가)
safe_json_get() {
  local key="$1"
  local input
  input=$(cat)
  # 1차: 문자열 값 — 이스케이프된 따옴표(\")를 건너뛰며 추출
  local val
  val=$(printf '%s' "$input" | tr '\n' ' ' | sed -n 's/.*"'"$key"'"[[:space:]]*:[[:space:]]*"\(\([^"\\]\|\\.\)*\)".*/\1/p' | head -1)
  if [ -n "$val" ]; then
    # 이스케이프 복원: \\ → \, \" → ", \n → 개행, \t → 탭
    # 핵심: \\\\ 를 플레이스홀더로 치환 → 다른 이스케이프 복원 → 플레이스홀더를 \ 로 복원
    # 이렇게 해야 \\n (리터럴\+n)이 개행으로 오변환되지 않음
    val=$(printf '%s' "$val" | sed 's/\\\\/\x00BSLASH\x00/g; s/\\"/"/g; s/\\n/\n/g; s/\\t/\t/g; s/\x00BSLASH\x00/\\/g')
    printf '%s' "$val"
    return 0
  fi
  # 2차: 객체/배열 값 — 첫 번째 { 또는 [ 부터 매칭
  val=$(printf '%s' "$input" | tr '\n' ' ' | sed -n 's/.*"'"$key"'"[[:space:]]*:[[:space:]]*\(\({[^}]*}\)\|\(\[.*\]\)\).*/\1/p' | head -1)
  if [ -n "$val" ]; then
    printf '%s' "$val"
    return 0
  fi
  # 3차: 원시 값 — true/false/null/숫자 (따옴표 없는 리터럴)
  val=$(printf '%s' "$input" | tr '\n' ' ' | sed -n 's/.*"'"$key"'"[[:space:]]*:[[:space:]]*\(true\|false\|null\|-\?[0-9][0-9.eE+-]*\)[[:space:]]*[,}].*/\1/p' | head -1)
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

# JSON 문자열 이스케이프: 백슬래시, 큰따옴표, 개행, CR, 탭 처리
# 사용법: SAFE="$(json_escape "$RAW_STRING")"
json_escape() {
  local s="$1"
  s=${s//\\/\\\\}
  s=${s//\"/\\\"}
  s=${s//$'\n'/\\n}
  s=${s//$'\r'/\\r}
  s=${s//$'\t'/\\t}
  printf '%s' "$s"
}

# 운영 중 누적되지만 완료 판정에서 무시할 런타임 산출물
is_volatile_runtime_path() {
  local path="$1"
  echo "$path" | grep -qE '^(\.claude/(incident_ledger\.jsonl|settings\.local\.json|settings\.local\.json\.bak_[0-9]+|command-audit\.log|subagent-audit\.log|tool-failure\.log|logs/|state/)|90_공통기준/토론모드/logs/)'
}

# 강한 완료 표현만 1차 트리거 (GPT+Claude 합의 2026-04-11 세션12)
# v8: 과감지 86.5% 해소 — "잔여 이슈 없", "ALL CLEAR", "GPT 판정: PASS" 단독 트리거 제거
# 이들은 completion_gate 내부에서 write_marker 존재 시 후속 조건으로만 사용
_COMPLETION_PATTERN='(완료 보고|최종[[:space:]]*(완료|반영)|모든[[:space:]]*작업[[:space:]]*완료|작업을[[:space:]]*모두[[:space:]]*마쳤|마무리됐습니다|final[[:space:]]+completion|work[[:space:]]+(is[[:space:]]+)?complete)'
# 후속 조건용 약한 패턴 (단독으로는 트리거하지 않음)
_COMPLETION_WEAK_PATTERN='(잔여[[:space:]]*이슈[[:space:]]*없(음|습니다)|ALL CLEAR|GPT 판정:[[:space:]]*PASS)'

is_completion_claim() {
  local text="$1"
  if [ -z "$text" ]; then
    return 1
  fi
  local matched
  matched=$(echo "$text" | grep -oiE "$_COMPLETION_PATTERN" | head -3 | tr '\n' '; ' | sed 's/; $//')
  if [ -n "$matched" ]; then
    hook_log "completion_claim" "matched_phrases=$matched" 2>/dev/null
    # GPT 합의 세션7: completion_claim 별도 로그 (로테이션 영향 없이 보존)
    local _cc_ts
    _cc_ts=$(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S')
    matched="${matched//\\/\\\\}"
    matched="${matched//\"/\\\"}"
    printf '{"ts":"%s","matched_phrases":"%s","source":"detect"}\n' "$_cc_ts" "$matched" \
      >> "$PROJECT_ROOT/.claude/logs/completion_claim.jsonl" 2>/dev/null
    return 0
  fi
  return 1
}

# evidence 공통: 세션 내 파일 신선도 판정 + evidence 디렉토리 설정
# evidence_gate.sh / evidence_stop_guard.sh 중복 제거 (GPT+Claude 합의 2026-04-11)
# 사용법: evidence_init → fresh_file/fresh_req/fresh_ok 사용 가능
evidence_init() {
  local sk
  sk=$(session_key)
  EVIDENCE_SESSION_DIR="$STATE_EVIDENCE/$sk"
  REQ_DIR="$EVIDENCE_SESSION_DIR/requires"
  PROOF_DIR="$EVIDENCE_SESSION_DIR/proofs"
  START_FILE="$EVIDENCE_SESSION_DIR/.session_start"
  mkdir -p "$REQ_DIR" "$PROOF_DIR"
  if [ ! -f "$START_FILE" ]; then
    : > "$START_FILE"
  fi
}

fresh_file() {
  local f="$1"
  [ -f "$f" ] && [ "$f" -nt "$START_FILE" ]
}

fresh_req() { fresh_file "$REQ_DIR/$1.req"; }
fresh_ok()  { fresh_file "$PROOF_DIR/$1.ok"; }

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

# Circuit breaker 최소형 — 동일 hook에서 unresolved incident 연속 N건 이상이면 경고
# 사용법: if circuit_breaker_tripped "hook_name" 3; then echo "WARN"; fi
# 반환: 0=tripped(경고 필요), 1=정상
circuit_breaker_tripped() {
  local target_hook="$1"
  local threshold="${2:-3}"
  [ ! -f "$INCIDENT_LEDGER" ] && return 1
  # 최근 20줄에서 해당 hook의 연속 unresolved 카운트
  local consecutive=0
  while IFS= read -r line; do
    local h r
    h=$(printf '%s' "$line" | safe_json_get "hook" 2>/dev/null)
    r=$(printf '%s' "$line" | safe_json_get "resolved" 2>/dev/null)
    if [ "$h" = "$target_hook" ]; then
      if [ "$r" = "false" ]; then
        consecutive=$((consecutive + 1))
      else
        consecutive=0
      fi
    fi
  done < <(tail -20 "$INCIDENT_LEDGER")
  [ "$consecutive" -ge "$threshold" ] && return 0
  return 1
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
  # 크기 경고: 512KB 초과 시 로그 (삭제는 하지 않음 — archive_resolved 수동 실행 유도)
  if [ -f "$INCIDENT_LEDGER" ]; then
    local _sz
    _sz=$(wc -c < "$INCIDENT_LEDGER" 2>/dev/null || echo 0)
    if [ "$_sz" -gt 512000 ] 2>/dev/null; then
      hook_log "incident" "WARN: incident_ledger ${_sz}B > 512KB — incident_repair.py --archive 실행 권장" 2>/dev/null || true
    fi
  fi
}
