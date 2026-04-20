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
  local GRACE_WINDOW=120
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
    hook_log "PreToolUse/evidence_gate" "incident suppress (fingerprint=$_fingerprint, grace=${GRACE_WINDOW}s, scan=100)" 2>/dev/null
    echo "[evidence_gate] 반복 차단 감지 (fp=$_fingerprint, 최근 ${GRACE_WINDOW}s 내 동일 사유). 차단 유지, 기록만 억제." >&2
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

# 세션78 P2 재정의 (Round 1 3자 합의): git commit만 검증 (push-only 면제)
#   기존(~세션77): risk_profile_prompt에서 tasks_handoff.req 조기 발행 → is_commit_or_push 시점에 검증 → 시간차로 맥락 상실
#   변경(세션78 초안): req 발행 제거, commit/push 감지 시 즉석 독립 검증 → 시간차 0
#   Round 1 합의 (GPT FAIL + Gemini 동의 + Claude 합의): push-only는 면제. git commit만 grep.
#     근거: git push는 이미 commit된 내역을 원격에 반영 — 문서 갱신 증거는 commit 시점에만 요구
#           세션76 commit_gate.sh의 push-only 스킵 최적화(체감 0.57s)와 정합
#           "문서=진실의 근원" 철학은 commit 단위에서 충분히 수호됨
#   has_any_req 우회 방지: early-exit을 이 블록 뒤로 이동시켰으므로 req 없는 세션에서도 commit 검증 동작
if echo "$COMMAND" | grep -qiE 'git commit'; then
  if ! fresh_ok "tasks_updated" || ! fresh_ok "handoff_updated"; then
    deny "commit 차단. 이번 세션에 TASKS.md/HANDOFF.md 갱신 흔적이 없습니다." "tasks_handoff"
  fi
fi

# req 없으면 완전 통과 — 일상 작업 마찰 방지 (세션78: commit/push 검증 이후로 이동)
if ! has_any_req; then
  hook_timing_end "evidence_gate" "$_EVG_START" "skip_noreq"
  exit 0
fi

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
# 세션78 P2 재정의: 스킬별 마커 skill_read__*.ok도 면제 대상에 포함
#   기존: fresh_ok "skill_read" || fresh_ok "identifier_ref"만 검사 → evidence_mark_read.sh가 생성하는 skill_read__${SKILL_ID}.ok 무시되는 모순
#   변경: 스킬별 마커가 세션에 하나라도 존재하면 통과 (재진입 사용자 흐름 존중)
if (fresh_req "skill_read" || fresh_req "identifier_ref") && is_identifier_domain_edit; then
  _has_skill_marker=false
  if fresh_ok "skill_read" || fresh_ok "identifier_ref"; then
    _has_skill_marker=true
  else
    for _m in "$PROOF_DIR"/skill_read__*.ok; do
      [ -e "$_m" ] || continue
      if [ "$_m" -nt "$START_FILE" ]; then
        _has_skill_marker=true
        break
      fi
    done
  fi
  if [ "$_has_skill_marker" = "false" ]; then
    deny "skill_read.req / identifier_ref.req 존재. SKILL.md 또는 기준정보 대조 없이 관련 도메인 수정 금지." "skill_read"
  fi
fi

# 4) 사고 품질 — 고위험 수정 시 map_scope 선행
# 세션77 Round 1 Step 1-c: 대상 파일 경로 체크 추가 (347건 71.4% 실증 기반 재정의)
#   - 기존: 모든 Write/Edit/MultiEdit 차단 → 문서·도메인 데이터 수정도 차단되는 과탐지
#   - 변경: Write/Edit 대상이 .claude/hooks/*.sh 또는 .claude/settings*.json일 때만 차단
#     ( .md / 데이터 파일 / 업무 스프레드시트 / 일반 스크립트는 map_scope 면제 )
if fresh_req "map_scope"; then
  if ! fresh_ok "map_scope"; then
    tool_name=$(echo "$INPUT" | safe_json_get "tool_name" 2>/dev/null || echo "")
    if echo "$tool_name" | grep -qiE '(Write|Edit|MultiEdit)'; then
      # 대상 파일 경로 추출 (safe_json_get은 top-level만 지원 → raw INPUT에서 직접 grep)
      target_file=$(printf '%s' "$INPUT" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
      # 운영 훅(.claude/hooks/*.sh) 또는 settings json만 차단 대상
      if echo "$target_file" | grep -qE '\.claude/hooks/[A-Za-z0-9_-]+\.sh$|\.claude/settings[A-Za-z0-9._-]*\.json$'; then
        deny "map_scope.req 존재. 변경 대상/연쇄 영향/후속 작업 3줄 선언(map_scope.ok) 없이 운영 훅·settings 수정 금지." "map_scope"
      fi
      # 기타 파일(.md, 데이터, 일반 스크립트 등)은 map_scope 면제 — 통과
    fi
  fi
fi

# 5) 종료 문서 갱신 선행 — 세션78 P2 재정의로 상단 commit/push 우선 검증 블록으로 이동
#   기존 조건 (fresh_req "tasks_handoff" && is_commit_or_push)은 req 조기 발행에 의존 → resolved 0% 초래
#   새 구조: deny() 정의 직후 블록에서 req 유무 무관 commit/push 단독 검증

hook_timing_end "evidence_gate" "$_EVG_START" "pass"
exit 0
