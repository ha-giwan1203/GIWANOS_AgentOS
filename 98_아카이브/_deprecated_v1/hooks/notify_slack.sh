#!/bin/bash
# Notification hook — Slack 알림 연동 (스팸 방지 포함)
source "$(dirname "$0")/hook_common.sh" 2>/dev/null
# 훅 등급: measurement (Phase 2-C 2026-04-19 세션73 timing 배선)
_NS_START=$(hook_timing_start)
INPUT=$(cat)
# safe_json_get 사용 (sed 단독 파싱 대체, GPT+Claude 합의 2026-04-11)
MSG=$(echo "$INPUT" | safe_json_get "message" 2>/dev/null)
MSG="${MSG:-알림}"

# 스팸 방지: 동일 메시지 60초 내 중복 전송 차단
DEDUP_FILE="$PROJECT_ROOT/.claude/hooks/.notify_dedup"
HASH=$(echo "$MSG" | md5sum | cut -d' ' -f1)
NOW=$(date +%s)

if [ -f "$DEDUP_FILE" ]; then
  LAST_HASH=$(head -1 "$DEDUP_FILE" 2>/dev/null)
  LAST_TIME=$(tail -1 "$DEDUP_FILE" 2>/dev/null)
  if [ "$HASH" = "$LAST_HASH" ] && [ $((NOW - LAST_TIME)) -lt 60 ]; then
    hook_timing_end "notify_slack" "$_NS_START" "skip_dedup"
    exit 0  # 중복 — 무시
  fi
fi

echo "$HASH" > "$DEDUP_FILE"
echo "$NOW" >> "$DEDUP_FILE"

hook_log "Notification" "$MSG" 2>/dev/null
# Slack 발송 — python3/python 동적 감지
PY_CMD=""
if command -v python3 >/dev/null 2>&1; then
  PY_CMD="python3"
elif command -v python >/dev/null 2>&1; then
  PY_CMD="python"
fi
if [ -n "$PY_CMD" ]; then
  $PY_CMD "$PROJECT_ROOT/90_공통기준/업무관리/slack_notify.py" --message "$MSG"
fi

hook_timing_end "notify_slack" "$_NS_START" "sent"
