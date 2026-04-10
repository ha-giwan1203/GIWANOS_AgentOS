#!/bin/bash
# completion-gate v7: 완료 주장 시 무조건 TASKS/HANDOFF 검증 + Git 미반영 차단
# GPT+Claude 토론 합의 2026-04-10: marker 우회 차단, 3단계 기준선
source "$(dirname "$0")/hook_common.sh" 2>/dev/null
hook_log "Stop" "completion_gate v7" 2>/dev/null || true

MARKER="$STATE_AGENT_CONTROL/write_marker.flag"
TASKS="$PATH_TASKS"
HANDOFF="$PATH_HANDOFF"

# 마지막 assistant 메시지가 "완료/최종반영" 주장일 때만 gate 적용
LAST_TEXT=$(last_assistant_text 2>/dev/null || true)
if ! is_completion_claim "$LAST_TEXT"; then
  exit 0
fi

# 기준선(baseline) 계산: marker 우선 → relevant change 최신 mtime → 없으면 통과
# 3단계 우선순위로 판정. Git 미반영 변경은 baseline 계산과 통합.
BASELINE=0
HAS_UNCOMMITTED="NO"

if [ -f "$MARKER" ]; then
  BASELINE=$(file_mtime "$MARKER")
fi

# Git 미반영 변경이 있으면 (1) 커밋 전이면 차단 + (2) baseline 후보로도 사용
if git_has_relevant_changes; then
  HAS_UNCOMMITTED="YES"
  while IFS= read -r rpath; do
    [ -z "$rpath" ] && continue
    fpath="$PROJECT_ROOT/$rpath"
    [ -f "$fpath" ] || continue
    mt=$(file_mtime "$fpath")
    [ "$mt" -gt "$BASELINE" ] 2>/dev/null && BASELINE="$mt"
  done <<RCEOF
$(git_relevant_change_list)
RCEOF
fi

# baseline이 0이면 marker도 없고 relevant change도 없음 → 통과
if [ "$BASELINE" -eq 0 ] 2>/dev/null; then
  exit 0
fi

# Git 미반영 변경이 남아 있으면 차단 (baseline 계산 후 판단)
if [ "$HAS_UNCOMMITTED" = "YES" ]; then
  CHANGES=$(git_relevant_change_list | head -n 3 | paste -sd, -)
  hook_incident "gate_reject" "completion_gate" "$CHANGES" "Git 미반영 변경이 남은 상태에서 완료 주장" '"classification_reason":"completion_before_git","next_action":"relevant change를 commit/push 또는 정리한 뒤 완료 보고 재시도"' 2>/dev/null || true
  echo "{\"decision\":\"block\",\"reason\":\"[COMPLETION GATE] Git 실물 변경이 아직 남아 있습니다: ${CHANGES}. 커밋/정리 후 완료로 보고하세요.\"}"
  exit 0
fi

MISSING=""
for NAME_PATH in "TASKS.md:$TASKS" "HANDOFF.md:$HANDOFF"; do
  NAME="${NAME_PATH%%:*}"
  FPATH="${NAME_PATH#*:}"
  if [ ! -f "$FPATH" ]; then
    MISSING="${MISSING}${MISSING:+,}$NAME"
    continue
  fi
  FILE_EPOCH=$(file_mtime "$FPATH")
  if [ "$FILE_EPOCH" -lt "$BASELINE" ] 2>/dev/null; then
    MISSING="${MISSING}${MISSING:+,}$NAME"
  fi
done

if [ -n "$MISSING" ]; then
  hook_incident "gate_reject" "completion_gate" "$MISSING" "완료 주장 전 ${MISSING} 미갱신" '"classification_reason":"completion_before_state_sync","next_action":"TASKS/HANDOFF를 최신 작업 상태로 갱신한 뒤 완료 보고 재시도"' 2>/dev/null || true
  echo "{\"decision\":\"block\",\"reason\":\"[COMPLETION GATE] 완료 보고 전 ${MISSING} 갱신이 필요합니다. 상태 문서를 먼저 갱신한 뒤 종료하세요.\"}"
else
  rm -f "$MARKER" 2>/dev/null
fi

exit 0
