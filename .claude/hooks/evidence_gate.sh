#!/bin/bash
# PreToolUse(Bash|Write|Edit|MultiEdit)
# req 파일이 있을 때만 활성. 증거 없는 위험 실행 차단.

source "$(dirname "$0")/hook_common.sh" 2>/dev/null

INPUT="$(cat)"

# hook_common.sh의 evidence_init() 사용 (중복 제거, GPT+Claude 합의 2026-04-11)
evidence_init

has_any_req() {
  find "$REQ_DIR" -maxdepth 1 -type f -name '*.req' -newer "$START_FILE" | grep -q .
}

# req 없으면 완전 통과 — 일상 작업 마찰 방지
if ! has_any_req; then
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

  # 중복 incident 억제: 동일 hook+reason+detail 직전 연속 3회 초과 시 기록 생략
  # GPT 보류→수정: grep -qF(고정문자열)이므로 sed 이스케이프 제거, 원문 그대로 비교
  local _dup_count=0
  local _reason_prefix
  _reason_prefix=$(printf '%s' "$reason" | head -c 80)
  if [ -f "$INCIDENT_LEDGER" ]; then
    # 직전 연속 카운트: 마지막 줄부터 역순으로 동일 패턴이 몇 줄 연속인지
    _dup_count=$(tail -20 "$INCIDENT_LEDGER" 2>/dev/null | tac 2>/dev/null | while IFS= read -r _line; do
      if echo "$_line" | grep -q '"hook":"evidence_gate".*"classification_reason":"evidence_missing"' && \
         echo "$_line" | grep -qF "$_reason_prefix"; then
        echo "match"
      else
        break
      fi
    done | wc -l)
  fi
  if [ "$_dup_count" -lt 3 ]; then
    hook_incident "gate_reject" "evidence_gate" "" "$reason" '"classification_reason":"evidence_missing"' 2>/dev/null || true
  else
    hook_log "PreToolUse/evidence_gate" "incident 중복 억제: 직전 연속 ${_dup_count}회 (3회 초과, detail일치)" 2>/dev/null
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

  echo "{\"decision\":\"deny\",\"reason\":\"[evidence_gate] ${reason}${resolve_hint}\"}"
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

exit 0
