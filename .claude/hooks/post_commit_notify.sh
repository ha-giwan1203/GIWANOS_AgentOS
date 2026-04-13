#!/bin/bash
# post_commit_notify.sh — git push 성공 후 Slack 자동 알림 (PostToolUse/Bash)
# GPT+Claude 합의 2026-04-13 세션34

source "$(dirname "$0")/hook_common.sh" 2>/dev/null || true

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | safe_json_get "command" 2>/dev/null)

# git push 성공 시에만 동작
if ! echo "$COMMAND" | grep -q 'git push'; then
  exit 0
fi

# exit_code 확인 — 0(성공)이 아니면 무시
EXIT_CODE=$(echo "$INPUT" | safe_json_get "exit_code" 2>/dev/null)
if [ "$EXIT_CODE" != "0" ] && [ -n "$EXIT_CODE" ]; then
  exit 0
fi

# 최신 커밋 SHA + 메시지 수집
SHA=$(git -C "$PROJECT_ROOT" log --oneline -1 2>/dev/null | head -1)
if [ -z "$SHA" ]; then
  exit 0
fi

MSG="커밋 푸시 완료: $SHA"

# Slack 발송 — python3/python 동적 감지
PY_CMD=""
if command -v python3 >/dev/null 2>&1; then
  PY_CMD="python3"
elif command -v python >/dev/null 2>&1; then
  PY_CMD="python"
fi

if [ -n "$PY_CMD" ]; then
  $PY_CMD "$PROJECT_ROOT/90_공통기준/업무관리/slack_notify.py" --message "$MSG" &
fi

hook_log "PostToolUse/Bash" "post_commit_notify: $MSG" 2>/dev/null
exit 0
