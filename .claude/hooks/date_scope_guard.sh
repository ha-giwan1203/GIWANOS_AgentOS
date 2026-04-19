#!/bin/bash
# PreToolUse(Bash) — ZDM/일상점검 위험 날짜 범위 차단
# 목적: 1~7 일괄, 일요일 포함, 애매한 MM/DD 범위를 사전 차단
#
# 훅 등급: gate (Phase 2-B 2026-04-19 세션72 명시화 + exit 2 전환)

source "$(dirname "$0")/hook_common.sh" 2>/dev/null

_DSG_START=$(hook_timing_start)
INPUT="$(cat)"
hook_log "PreToolUse/Bash" "date_scope_guard 발화"

COMMAND="$(echo "$INPUT" | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\(.*\)".*/\1/p' | head -1)"

# ZDM/일상점검 관련 명령이 아니면 통과
if ! echo "$COMMAND" | grep -qiE '(zdm|daily[-_ ]inspection|일상점검|점검표|backfill)'; then
  hook_timing_end "date_scope_guard" "$_DSG_START" "skip_nonzdm"
  exit 0
fi

deny() {
  local reason="$1"
  hook_log "PreToolUse/date_scope_guard" "BLOCK: $reason | $COMMAND"
  hook_incident "gate_reject" "date_scope_guard" "" "$reason" '"classification_reason":"scope_violation"' 2>/dev/null || true
  local safe_reason
  safe_reason=$(json_escape "[date_scope_guard] $reason")
  echo "{\"hookSpecificOutput\":{\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"$safe_reason\"}}"
  hook_timing_end "date_scope_guard" "$_DSG_START" "block"
  exit 2
}

# 1~7 / 1-7 / 1..7 류 직접 차단
if echo "$COMMAND" | grep -qE '(^|[^0-9])1[[:space:]]*[-~][[:space:]]*7([^0-9]|$)|1\.\.7|1 to 7'; then
  deny "1~7 일괄 범위 감지. 명시 날짜 확인 없이 ZDM/일상점검 일괄 실행 금지."
fi

# MM/DD 같은 애매한 날짜는 차단하고 YYYY-MM-DD 요구
if echo "$COMMAND" | grep -qE '(^|[^0-9])[0-9]{1,2}/[0-9]{1,2}([^0-9]|$)'; then
  deny "MM/DD 형식 감지. YYYY-MM-DD 명시 또는 date_check 선행 후 재실행."
fi

DATES="$(printf '%s\n' "$COMMAND" | grep -oE '[0-9]{4}[./-][0-9]{1,2}[./-][0-9]{1,2}' | tr './' '--' | sed 's/--/-/g' | sort -u)"

# 날짜별 일요일 차단
if [ -n "$DATES" ]; then
  for d in $DATES; do
    dow="$(date -d "$d" +%u 2>/dev/null || echo '')"
    if [ "$dow" = "7" ]; then
      deny "일요일($d) 포함 감지. 요일 확인 없이 ZDM/일상점검 실행 금지."
    fi
  done
fi

hook_timing_end "date_scope_guard" "$_DSG_START" "pass"
exit 0
