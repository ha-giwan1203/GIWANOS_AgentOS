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

TRIGGER_HITS=$(echo "$HEAD_FILES" | grep -E '^\.claude/(hooks|commands|agents)/|^\.claude/settings.*\.json$|^90_공통기준/스킬/.+/SKILL\.md$|^CLAUDE\.md$|/CLAUDE\.md$' || true)

if [ -z "$TRIGGER_HITS" ]; then
  exit 0
fi

# 기록
LOG_DIR="$PROJECT_DIR/.claude/state"
LOG_FILE="$LOG_DIR/mode_c_log.jsonl"
mkdir -p "$LOG_DIR" 2>/dev/null

SHA=$(git rev-parse --short HEAD 2>/dev/null)
# v2 (debate_20260428_080046_3way Round 1 PASS): 멀티바이트 안전 cut — Python 문자 단위 슬라이스 + .strip() (개행/공백 제거)
# fallback: PY_CMD 미정의 시 python (hook_common.sh source 실패 대비)
SUBJECT=$(git log -1 --pretty=%s 2>/dev/null | tr -d '"' | "${PY_CMD:-python}" -c "import sys; data=sys.stdin.buffer.read().decode('utf-8',errors='replace'); sys.stdout.buffer.write(data.strip()[:120].encode('utf-8'))" 2>/dev/null)
TS=$(date -u "+%Y-%m-%dT%H:%M:%SZ" 2>/dev/null)
TRIGGERS_JSON=$(echo "$TRIGGER_HITS" | head -10 | awk 'BEGIN{ORS=""} NR>1{print ","} {gsub(/"/,"\\\""); print "\""$0"\""}')

LINE="{\"ts\":\"$TS\",\"sha\":\"$SHA\",\"trigger_files\":[$TRIGGERS_JSON],\"commit_subject\":\"$SUBJECT\"}"
echo "$LINE" >> "$LOG_FILE" 2>/dev/null || true

echo "[mode_c_log] 기록됨: SHA $SHA — C 트리거 $(echo "$TRIGGER_HITS" | wc -l | tr -d ' ')건" >&2
hook_log "PostToolUse/Bash" "mode_c_log: recorded sha=$SHA" 2>/dev/null || true

# v2 회전 블록 (debate_20260428_080046_3way Round 1 PASS): 256KB 임계 archive 분리
# 패턴 B (incident_ledger.archive 선례). oldest 50% → mode_c_log.archive.jsonl 이동, in-place는 newest 50% 보존.
# Gemini 보강: 임시 파일 + mv로 원자적 교체 (POSIX mv 원자성 보장 — I/O 경합 방어).
ROT_THRESHOLD=262144  # 256KB
if [ -f "$LOG_FILE" ]; then
  LOG_SIZE=$(wc -c < "$LOG_FILE" 2>/dev/null || echo 0)
  if [ "$LOG_SIZE" -gt "$ROT_THRESHOLD" ] 2>/dev/null; then
    ARCHIVE_FILE="$LOG_DIR/mode_c_log.archive.jsonl"
    TOTAL_LINES=$(wc -l < "$LOG_FILE" 2>/dev/null || echo 0)
    HALF=$((TOTAL_LINES / 2))
    if [ "$HALF" -gt 0 ]; then
      TMP_NEW="${LOG_FILE}.tmp.$$"
      head -n "$HALF" "$LOG_FILE" >> "$ARCHIVE_FILE" 2>/dev/null
      tail -n +$((HALF + 1)) "$LOG_FILE" > "$TMP_NEW" 2>/dev/null && mv "$TMP_NEW" "$LOG_FILE" 2>/dev/null
      hook_log "PostToolUse/Bash" "mode_c_log: rotated $HALF lines → archive (size was ${LOG_SIZE}B)" 2>/dev/null || true
    fi
  fi
fi

exit 0
