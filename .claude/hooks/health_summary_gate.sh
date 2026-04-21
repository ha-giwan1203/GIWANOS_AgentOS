#!/bin/bash
# Self-X Layer 1 — UserPromptSubmit health summary gate
# 출처: debate_20260421_133506_3way (M3 gate 격상)
# 등급: advisory (현재 단계 — Phase 2-C에서 hard gate 검토)
# 정책: M3 보강 프롬프트 자동 주입 / M4 단순 인사·확인 면제
#
# 동작: Claude의 응답 자체는 검사 불가 → 첫 사용자 메시지 시점에 health summary 의무
#       리마인더를 stderr로 주입. 단순 인사·확인은 면제.

set +e

source "$(dirname "$0")/hook_common.sh"
_HSG_START=$(hook_timing_start)

INPUT=$(cat)
PROMPT=$(printf '%s' "$INPUT" | safe_json_get "prompt" 2>/dev/null || echo "")

# M4: 단순 인사·확인 감지 시 면제
SIMPLE_PATTERN='^(안녕|hi|hello|테스트|test|확인|ok|네$|예$|좋아|좋습니다|감사|고마워|뭐해|뭐해\?|상태\?|reset|clear|/help|/status)'
if echo "$PROMPT" | head -1 | grep -qiE "$SIMPLE_PATTERN"; then
  hook_log "health_summary_gate" "exempt simple_greeting"
  hook_timing_end "health_summary_gate" "$_HSG_START" "advisory"
  exit 0
fi

# 짧은 메시지(20자 미만) 면제
PROMPT_LEN=${#PROMPT}
if [ "$PROMPT_LEN" -lt 20 ]; then
  hook_log "health_summary_gate" "exempt short_msg len=$PROMPT_LEN"
  hook_timing_end "health_summary_gate" "$_HSG_START" "advisory"
  exit 0
fi

# 세션 첫 사용자 메시지인지 확인
FIRST_MARKER="$PROJECT_ROOT/.claude/state/health_summary_first.ok"
if [ -f "$FIRST_MARKER" ]; then
  # 이미 첫 메시지 처리됨 — pass
  hook_timing_end "health_summary_gate" "$_HSG_START" "advisory"
  exit 0
fi

# 첫 메시지: health summary 의무 리마인더 주입
SUMMARY_FILE="$PROJECT_ROOT/.claude/self/summary.txt"
if [ -f "$SUMMARY_FILE" ]; then
  SUMMARY=$(cat "$SUMMARY_FILE" | head -1)
  echo "" >&2
  echo "[health-summary-gate] Claude 첫 응답에 다음 health summary 1줄을 포함해야 합니다:" >&2
  echo "  $SUMMARY" >&2
  echo "  WARN/CRITICAL이 있으면 자동 펼침. 상세는 .claude/self/HEALTH.md 참조." >&2
  echo "" >&2
  hook_log "health_summary_gate" "reminder_injected summary=$SUMMARY"
fi

touch "$FIRST_MARKER"
hook_timing_end "health_summary_gate" "$_HSG_START" "advisory"
exit 0
