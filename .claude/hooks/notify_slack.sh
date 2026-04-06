#!/bin/bash
# Notification hook — Slack 알림 연동 (스팸 방지 포함)
source "$(dirname "$0")/hook_common.sh" 2>/dev/null
INPUT=$(cat)
MSG=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('message','알림'))" 2>/dev/null || echo "알림")

# 스팸 방지: 동일 메시지 60초 내 중복 전송 차단
DEDUP_FILE="$HOME/Desktop/업무리스트/.claude/hooks/.notify_dedup"
HASH=$(echo "$MSG" | md5sum | cut -d' ' -f1)
NOW=$(date +%s)

if [ -f "$DEDUP_FILE" ]; then
  LAST_HASH=$(head -1 "$DEDUP_FILE" 2>/dev/null)
  LAST_TIME=$(tail -1 "$DEDUP_FILE" 2>/dev/null)
  if [ "$HASH" = "$LAST_HASH" ] && [ $((NOW - LAST_TIME)) -lt 60 ]; then
    exit 0  # 중복 — 무시
  fi
fi

echo "$HASH" > "$DEDUP_FILE"
echo "$NOW" >> "$DEDUP_FILE"

hook_log "Notification" "$MSG" 2>/dev/null
# Slack 발송 (활성화 시 주석 해제)
# python3 "$HOME/Desktop/업무리스트/90_공통기준/업무관리/slack_notify.py" --message "$MSG"
