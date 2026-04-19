#!/bin/bash
# PreToolUse(Bash|Write|Edit|MultiEdit)
# req 파일이 있을 때만 활성. 증거 없는 위험 실행 차단.

source "$(dirname "$0")/hook_common.sh" 2>/dev/null
# 훅 등급: gate (Phase 2-C 2026-04-19 세션73 timing 배선, exit 2 승격은 1주 수집 후)
_EVG_START=$(hook_timing_start)

INPUT="$(cat)"

# hook_common.sh의 evidence_init() 사용 (중복 제거, GPT+Claude 합의 2026-04-11)
evidence_init

has_any_req() {
  find "$REQ_DIR" -maxdepth 1 -type f -name '*.req' -newer "$START_FILE" | grep -q .
}

# req 없으면 완전 통과 — 일상 작업 마찰 방지
if ! has_any_req; then
  hook_timing_end "evidence_gate" "$_EVG_START" "skip_noreq"
  exit 0
fi

# safe_json_get 사용 (sed 직접 파싱 대체, 세션14 GPT 합의)
COMMAND="$(echo "$INPUT" | safe_json_get "command" 2>/dev/null)"
TEXT="$(echo "$INPUT" | safe_json_get "tool_input" 2>/dev/null)"
if [ -z "$TEXT" ]; then
  TEXT="$(printf '%s' "$INPUT" | tr '\n' ' ')"
fi

is_bash_risky_date() {
  echo "$COMMAND" | grep -qiE '(zdm|daily[-_ ]inspection|일상점검|점검표|backfill)'
}

is_bash_risky_auth() {
  echo "$COMMAND" | grep -qiE '(mes|login|oauth|auth-dev|redirect|selenium|chrome)'
}

is_commit_or_push() {
  echo "$COMMAND" | grep -qiE 'git commit|git push'
}

is_identifier_domain_edit() {
  echo "$TEXT" | grep -qiE '(10_라인배치/|90_공통기준/스킬/|production-result-upload|zdm-daily-inspection|기준정보|SKILL\.md|CLAUDE\.md)'
}

deny() {
  local reason="$1"
  local req_name="$2"  # optional: 해결 방법 안내용 req 이름
  hook_log "PreToolUse/evidence_gate" "BLOCK: $reason"

  # fingerprint 기반 incident suppress (GPT+Claude 합의 세션43):
  # fingerprint = hash(reason_prefix|command_prefix) — 사건 동일성 판별
  # 동일 fingerprint가 GRACE_WINDOW초 이내에 이미 기록된 경우 → 기록 생략 (차단은 유지)
  local GRACE_WINDOW=30
  local _fp_raw
  _fp_raw="${reason:0:80}|${COMMAND:0:50}"
  local _fingerprint
  if command -v sha1sum >/dev/null 2>&1; then
    _fingerprint=$(printf '%s' "$_fp_raw" | sha1sum | cut -c1-16)
  elif command -v md5sum >/dev/null 2>&1; then
    _fingerprint=$(printf '%s' "$_fp_raw" | md5sum | cut -c1-16)
  else
    _fingerprint=$(printf '%s' "$_fp_raw" | cksum | awk '{print $1}' | cut -c1-16)
  fi

  local _should_record=true
  if [ -f "$INCIDENT_LEDGER" ]; then
    local _now _cutoff
    _now=$(date +%s 2>/dev/null || echo 0)
    _cutoff=$((_now - GRACE_WINDOW))
    while IFS= read -r _line; do
      local _fp_in_line _ts_in_line _epoch
      _fp_in_line=$(printf '%s' "$_line" | safe_json_get "fingerprint" 2>/dev/null)
      if [ "$_fp_in_line" = "$_fingerprint" ]; then
        _ts_in_line=$(printf '%s' "$_line" | safe_json_get "ts" 2>/dev/null)
        _epoch=$(date -d "$_ts_in_line" +%s 2>/dev/null || \
                 date -jf "%Y-%m-%dT%H:%M:%SZ" "$_ts_in_line" +%s 2>/dev/null || echo 0)
        if [ "$_epoch" -gt "$_cutoff" ] 2>/dev/null; then
          _should_record=false
          break
        fi
      fi
    done < <(tail -30 "$INCIDENT_LEDGER")
  fi

  if [ "$_should_record" = "true" ]; then
    hook_incident "gate_reject" "evidence_gate" "" "$reason" \
      "\"classification_reason\":\"evidence_missing\",\"fingerprint\":\"$_fingerprint\"" 2>/dev/null || true
  else
    hook_log "PreToolUse/evidence_gate" "incident suppress (fingerprint=$_fingerprint, grace=${GRACE_WINDOW}s)" 2>/dev/null
  fi

  # 해결 방법 안내 포함 (사용자가 탈출 경로를 알 수 있도록)
  local resolve_hint=""
  if [ "$req_name" = "map_scope" ]; then
    resolve_hint=" 해결: /map-scope 실행 또는 변경 대상/연쇄 영향/후속 작업 3줄을 직접 선언하면 ok 마커가 생성됩니다."
  elif [ "$req_name" = "date_check" ]; then
    resolve_hint=" 해결: date 명령으로 현재 날짜를 확인하면 date_check.ok가 생성됩니다."
  elif [ "$req_name" = "tasks_handoff" ]; then
    resolve_hint=" 해결: TASKS.md와 HANDOFF.md를 갱신하면 ok 마커가 생성됩니다."
  fi

  local _safe_msg
  _safe_msg=$(json_escape "[evidence_gate] ${reason}${resolve_hint}")
  echo "{\"hookSpecificOutput\":{\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"$_safe_msg\"}}"
  hook_timing_end "evidence_gate" "$_EVG_START" "block_${req_name:-unknown}"
  exit 0
}

# 1) 날짜 검증 선행
if fresh_req "date_check" && is_bash_risky_date; then
  if ! fresh_ok "date_check"; then
    deny "date_check.req 존재. date_check.ok 없이 날짜 관련 실행 금지." "date_check"
  fi
fi

# 2) 로그인/실패 진단 선행
if fresh_req "auth_diag" && is_bash_risky_auth; then
  # 진단 스크립트 자체 실행은 허용
  if ! echo "$COMMAND" | grep -qiE 'auth_diag(\.sh)?'; then
    if ! fresh_ok "auth_diag"; then
      deny "auth_diag.req 존재. auth_diag.ok 없이 MES/OAuth 관련 실행 금지." "auth_diag"
    fi
  fi
fi

# 3) 식별자/기준 문서 선행
if (fresh_req "skill_read" || fresh_req "identifier_ref") && is_identifier_domain_edit; then
  if ! fresh_ok "skill_read" && ! fresh_ok "identifier_ref"; then
    deny "skill_read.req / identifier_ref.req 존재. SKILL.md 또는 기준정보 대조 없이 관련 도메인 수정 금지." "skill_read"
  fi
fi

# 4) 사고 품질 — 고위험 수정 시 map_scope 선행
if fresh_req "map_scope"; then
  if ! fresh_ok "map_scope"; then
    # Write/Edit/MultiEdit만 차단 (Bash read 등은 허용)
    tool_name=$(echo "$INPUT" | safe_json_get "tool_name" 2>/dev/null || echo "")
    if echo "$tool_name" | grep -qiE '(Write|Edit|MultiEdit)'; then
      deny "map_scope.req 존재. 변경 대상/연쇄 영향/후속 작업 3줄 선언(map_scope.ok) 없이 고위험 수정 금지." "map_scope"
    fi
  fi
fi

# 5) 종료 문서 갱신 선행 — commit/push 전만 체크
if fresh_req "tasks_handoff" && is_commit_or_push; then
  if ! fresh_ok "tasks_updated" || ! fresh_ok "handoff_updated"; then
    deny "tasks_handoff.req 존재. TASKS/HANDOFF 갱신 없이 commit/push 금지." "tasks_handoff"
  fi
fi

hook_timing_end "evidence_gate" "$_EVG_START" "pass"
exit 0
