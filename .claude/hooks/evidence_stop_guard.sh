#!/bin/bash
# Stop — req 기반으로만 활성. 근거 없는 최종 결론 차단.
#
# 훅 등급: gate (기존부터 exit 2 사용 — Phase 2-B 2026-04-19 세션72 timing + 헤더 추가)

source "$(dirname "$0")/hook_common.sh" 2>/dev/null
_ESG_START=$(hook_timing_start)
hook_log "Stop" "evidence_stop_guard 발화" 2>/dev/null

TRANSCRIPT="$CLAUDE_TRANSCRIPT_PATH"

# hook_common.sh의 evidence_init() 사용 (중복 제거, GPT+Claude 합의 2026-04-11)
evidence_init

has_any_req() {
  find "$REQ_DIR" -maxdepth 1 -type f -name '*.req' -newer "$START_FILE" | grep -q .
}

if [ -z "$TRANSCRIPT" ] || [ ! -f "$TRANSCRIPT" ]; then
  hook_timing_end "evidence_stop_guard" "$_ESG_START" "skip_notranscript"
  exit 0
fi

if ! has_any_req; then
  hook_timing_end "evidence_stop_guard" "$_ESG_START" "skip_noreq"
  exit 0
fi

# last_assistant_text() 공용 함수 사용 (GPT 제안, 세션19 리팩토링)
LAST_TEXT=$(last_assistant_text 2>/dev/null || true)
if [ -z "$LAST_TEXT" ]; then
  hook_timing_end "evidence_stop_guard" "$_ESG_START" "skip_notext"
  exit 0
fi

block() {
  local reason="$1"
  hook_log "Stop/evidence_stop_guard" "BLOCK: $reason" 2>/dev/null
  hook_incident "hook_block" "evidence_stop_guard" "" "$reason" '"classification_reason":"evidence_missing"' 2>/dev/null || true
  echo "{\"decision\":\"block\",\"reason\":\"[evidence_stop_guard] $reason\"}"
  hook_timing_end "evidence_stop_guard" "$_ESG_START" "block"
  exit 2
}

# 1) 로그인 실패/수동 로그인 주장
if fresh_req "auth_diag"; then
  if echo "$LAST_TEXT" | grep -qiE '(로그인 실패|실패로 판단|수동 로그인|직접 로그인 필요|사용자가 로그인)'; then
    if ! fresh_ok "auth_diag"; then
      block "auth_diag.req 존재. auth_diag.ok 없이 로그인 실패/수동 로그인 결론 금지."
    fi
  fi
fi

# 2) 식별자 불일치 주장
if fresh_req "skill_read" || fresh_req "identifier_ref"; then
  if echo "$LAST_TEXT" | grep -qiE '(아이디가 다르|계정이 다르|식별자 불일치|품번 불일치|기준정보와 다르)'; then
    if ! fresh_ok "skill_read" && ! fresh_ok "identifier_ref"; then
      block "skill_read.req / identifier_ref.req 존재. SKILL.md 또는 기준정보 대조 없이 불일치 결론 금지."
    fi
  fi
fi

# 3) 완료/반영 완료/PASS 주장
if fresh_req "tasks_handoff"; then
  if echo "$LAST_TEXT" | grep -qiE '(완료|반영 완료|수정 완료|PASS)'; then
    if ! fresh_ok "tasks_updated" || ! fresh_ok "handoff_updated"; then
      block "tasks_handoff.req 존재. TASKS/HANDOFF 갱신 없이 완료/PASS 결론 금지."
    fi
  fi
fi

hook_timing_end "evidence_stop_guard" "$_ESG_START" "pass"
exit 0
