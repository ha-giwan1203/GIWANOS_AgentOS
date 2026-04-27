#!/bin/bash
# mode_c_log.sh — C 트리거 커밋 성공 후 mode_c_log.jsonl 기록 (advisory)
# 별건 3번 (세션118 신설). HANDOFF 자동 직접 수정은 무한 루프 위험으로 회피 — state 파일 + stderr 알림.
# 훅 등급: advisory. exit 0 강제.

source "$(dirname "$0")/hook_common.sh" 2>/dev/null || true

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | safe_json_get "command")

# git commit 미감지 → skip
if ! echo "${COMMAND:-$INPUT}" | grep -qE 'git (commit)'; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$PROJECT_DIR" 2>/dev/null || exit 0

# 직전 커밋(HEAD) 변경 파일 — PostToolUse 시점에는 commit 완료 상태
HEAD_FILES=$(git show --pretty="" --name-only HEAD 2>/dev/null)
[ -z "$HEAD_FILES" ] && exit 0

TRIGGER_HITS=$(echo "$HEAD_FILES" | grep -E '^\.claude/(hooks|settings.*\.json|commands|agents)/|^90_공통기준/스킬/.+/SKILL\.md$|^CLAUDE\.md$|/CLAUDE\.md$' || true)

if [ -z "$TRIGGER_HITS" ]; then
  exit 0
fi

# 기록
LOG_DIR="$PROJECT_DIR/.claude/state"
LOG_FILE="$LOG_DIR/mode_c_log.jsonl"
mkdir -p "$LOG_DIR" 2>/dev/null

SHA=$(git rev-parse --short HEAD 2>/dev/null)
SUBJECT=$(git log -1 --pretty=%s 2>/dev/null | tr -d '"' | cut -c1-120)
TS=$(date -u "+%Y-%m-%dT%H:%M:%SZ" 2>/dev/null)
TRIGGERS_JSON=$(echo "$TRIGGER_HITS" | head -10 | awk 'BEGIN{ORS=""} NR>1{print ","} {gsub(/"/,"\\\""); print "\""$0"\""}')

LINE="{\"ts\":\"$TS\",\"sha\":\"$SHA\",\"trigger_files\":[$TRIGGERS_JSON],\"commit_subject\":\"$SUBJECT\"}"
echo "$LINE" >> "$LOG_FILE" 2>/dev/null || true

echo "[mode_c_log] 기록됨: SHA $SHA — C 트리거 $(echo "$TRIGGER_HITS" | wc -l | tr -d ' ')건" >&2
hook_log "PostToolUse/Bash" "mode_c_log: recorded sha=$SHA" 2>/dev/null || true

exit 0
