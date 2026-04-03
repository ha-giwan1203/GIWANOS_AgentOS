#!/bin/bash
# session-preflight: 세션 시작 시 핵심 상태 문서 실물 검증
# - TASKS.md, STATUS.md, HANDOFF.md 존재 여부
# - 각 파일 최종 수정일 (7일 이상 미갱신 시 경고)
# - 합의: GPT+Claude 2026-04-01
source "$(dirname "$0")/hook_common.sh" 2>/dev/null
hook_log "SessionStart" "session_preflight 발화" 2>/dev/null

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
TASKS="$PROJECT_DIR/90_공통기준/업무관리/TASKS.md"
STATUS="$PROJECT_DIR/90_공통기준/업무관리/STATUS.md"
HANDOFF="$PROJECT_DIR/90_공통기준/업무관리/HANDOFF.md"

errors=()
warnings=()

# 파일 존재 검증
for f in "$TASKS" "$STATUS" "$HANDOFF"; do
  fname=$(basename "$f")
  if [ ! -f "$f" ]; then
    errors+=("$fname 파일 없음")
  else
    # 최종 수정일 확인 (7일 이상 미갱신 경고)
    if command -v stat &>/dev/null; then
      mod_epoch=$(stat -c %Y "$f" 2>/dev/null || stat -f %m "$f" 2>/dev/null)
      now_epoch=$(date +%s)
      if [ -n "$mod_epoch" ]; then
        diff_days=$(( (now_epoch - mod_epoch) / 86400 ))
        if [ "$diff_days" -gt 7 ]; then
          warnings+=("$fname ${diff_days}일 미갱신")
        fi
      fi
    fi
  fi
done

# 결과 출력
if [ ${#errors[@]} -gt 0 ]; then
  msg="[PREFLIGHT FAIL] ${errors[*]}"
  if [ ${#warnings[@]} -gt 0 ]; then
    msg="$msg | 경고: ${warnings[*]}"
  fi
  echo "{\"message\":\"$msg\"}"
  exit 2  # Claude에게 재고 요청
fi

if [ ${#warnings[@]} -gt 0 ]; then
  echo "{\"message\":\"[PREFLIGHT WARN] ${warnings[*]} — 갱신 필요 여부 확인할 것\"}"
  exit 0
fi

echo "{\"message\":\"[PREFLIGHT OK] TASKS/STATUS/HANDOFF 실물 확인 완료\"}"
exit 0
