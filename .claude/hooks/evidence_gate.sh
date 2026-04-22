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

# 세션78 P2 재정의: has_any_req early-exit은 deny() 정의 이후로 이동됨
#   이유: commit/push 검증을 req 유무와 무관하게 우선 수행하기 위함
#   (tasks_handoff.req 조기 발행 제거로 인한 has_any_req 우회 방지)

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

  # fingerprint 기반 incident suppress (GPT+Claude 합의 세션43, 세션83 Round 2 확장):
  # fingerprint = hash(reason_prefix|command_prefix) — 사건 동일성 판별
  # 동일 fingerprint가 GRACE_WINDOW초 이내에 이미 기록된 경우 → 기록 생략 (차단은 유지)
  #
  # 세션83 Round 2 (4개 확장추론 모델 만장일치 — API 예외 토론):
  #   실측: 04-19 165건 중 fp 상위 3종 66% 집중, 반복 간격 30~90초
  #   기존 GRACE_WINDOW=30·tail -30은 경계선 탈출 + 다른 fp 혼재 시 suppress 실패
  #   변경: GRACE_WINDOW 30→120, tail -30→-100 (차단은 유지, 기록 중복만 확장 억제)
  #   금지(4자 합의): fresh_ok 완화, cooldown 중 차단 생략 — 역방향 위험
  #
  # 세션86 (2026-04-21, Case A — 2자 토론 GPT 조건부 통과 수정 반영):
  #   실측 보고서: 90_공통기준/업무관리/incident_improvement_20260421_session86.md
  #   7일 evidence_gate 미해결 272건 / 동일 fp 연속 간격 249샘플 / GRACE=120 설계가 81.5% 반복 놓침
  #   median 347s, Top3 fp(7일 194건=71%) median 320~370s, over-120 82~93%
  #   변경: GRACE_WINDOW 120→300 (120~300 구간 회수 목적, 기대 억제율 18.5%→46.2% 2.5배)
  #   경계: 299s 이내 동일 fp → suppress / 301s 이상 → record
  #   불변: deny 경로, fingerprint 정의(reason:0:80|command:0:50), fresh_ok 역방향 방어
  local GRACE_WINDOW=300
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
    done < <(tail -100 "$INCIDENT_LEDGER")
  fi

  if [ "$_should_record" = "true" ]; then
    hook_incident "gate_reject" "evidence_gate" "" "$reason" \
      "\"classification_reason\":\"evidence_missing\",\"fingerprint\":\"$_fingerprint\"" 2>/dev/null || true
  else
    # 세션91 단계 III-2 (2026-04-22): suppress 라벨 hook_log/stderr 고정.
    # suppress_reason=evidence_recent — 이 경로는 사전 근거 범위 내 중복 억제일 뿐,
    # incident_ledger row를 생성하지 않는다 (suppress 의미 파괴 방지).
    hook_log "PreToolUse/evidence_gate" "incident suppress (suppress_reason=evidence_recent, fingerprint=$_fingerprint, grace=${GRACE_WINDOW}s, scan=100)" 2>/dev/null
    echo "[evidence_gate] suppress_reason=evidence_recent — 반복 차단 감지 (fp=$_fingerprint, 최근 ${GRACE_WINDOW}s 내 동일 사유). 차단 유지, 기록만 억제." >&2
  fi

  # 해결 방법 안내 포함 (사용자가 탈출 경로를 알 수 있도록)
  # 세션93 (2026-04-22 2자 토론 합의, plan.md 1주차 4번):
  #   evidence-core 3종(date_check / auth_diag / identifier_ref)만 resolve_hint 제공
  #   map_scope / tasks_handoff / skill_read 힌트는 해당 블록과 함께 제거됨
  local resolve_hint=""
  if [ "$req_name" = "date_check" ]; then
    resolve_hint=" 해결: date 명령으로 현재 날짜를 확인하면 date_check.ok가 생성됩니다."
  elif [ "$req_name" = "auth_diag" ]; then
    resolve_hint=" 해결: auth_diag 스크립트 실행 또는 수동 로그인 진단 수행 시 auth_diag.ok가 생성됩니다."
  elif [ "$req_name" = "identifier_ref" ]; then
    resolve_hint=" 해결: 기준정보 대조 수행 시 identifier_ref.ok가 생성됩니다."
  fi

  local _safe_msg
  _safe_msg=$(json_escape "[evidence_gate] ${reason}${resolve_hint}")
  echo "{\"hookSpecificOutput\":{\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"$_safe_msg\"}}"
  hook_timing_end "evidence_gate" "$_EVG_START" "block_${req_name:-unknown}"
  exit 0
}

# 세션93 (2026-04-22 2자 토론 합의, plan.md 1주차 4번 체크리스트 (a)):
#   tasks_handoff 검증 블록 제거 — commit_gate/final_check + completion_gate로 책임 이관 완료
#   - commit_gate.sh: PreToolUse Bash 매처에서 final_check --fast 호출 (세션76 push-only skip 포함)
#   - final_check.sh: "--- 7. TASKS/HANDOFF 갱신 확인 ---" + after_state_sync 검증 (line 330~)
#   - completion_gate.sh: Stop 훅에서 write_marker + after_state_sync + git_has_relevant_changes
#   따라서 evidence_gate에서 commit 시 tasks_updated/handoff_updated fresh_ok 재검증 불필요
# 세션93 체크리스트 (b):
#   map_scope 차단 블록 제거 — evidence 버스에서 분리. /map-scope 스킬은 Claude 자발적 선언 경로로 유지
# 세션93 체크리스트 (c):
#   skill_read 그룹 제거 — skill_instruction_gate로 이관. identifier_ref는 evidence-core 유지

# req 없으면 완전 통과 — 일상 작업 마찰 방지
if ! has_any_req; then
  hook_timing_end "evidence_gate" "$_EVG_START" "skip_noreq"
  exit 0
fi

# 1) 날짜 검증 선행 (evidence-core)
if fresh_req "date_check" && is_bash_risky_date; then
  if ! fresh_ok "date_check"; then
    deny "date_check.req 존재. date_check.ok 없이 날짜 관련 실행 금지." "date_check"
  fi
fi

# 2) 로그인/실패 진단 선행 (evidence-core)
if fresh_req "auth_diag" && is_bash_risky_auth; then
  # 진단 스크립트 자체 실행은 허용
  if ! echo "$COMMAND" | grep -qiE 'auth_diag(\.sh)?'; then
    if ! fresh_ok "auth_diag"; then
      deny "auth_diag.req 존재. auth_diag.ok 없이 MES/OAuth 관련 실행 금지." "auth_diag"
    fi
  fi
fi

# 3) 식별자/기준 문서 선행 (evidence-core)
# 세션93: skill_read 분리 → skill_instruction_gate가 SKILL.md 읽기 전담. 여기는 identifier_ref만 검증
if fresh_req "identifier_ref" && is_identifier_domain_edit; then
  if ! fresh_ok "identifier_ref"; then
    deny "identifier_ref.req 존재. 기준정보 대조(identifier_ref.ok) 없이 관련 도메인 수정 금지." "identifier_ref"
  fi
fi

hook_timing_end "evidence_gate" "$_EVG_START" "pass"
exit 0
