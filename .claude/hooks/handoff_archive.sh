#!/bin/bash
# handoff_archive.sh — HANDOFF.md 자동 아카이브 (PostToolUse Write|Edit)
# GPT+Claude 토론 합의 세션7: HANDOFF 400줄 초과 시 최신 2세션 유지, 나머지 아카이브
source "$(dirname "$0")/hook_common.sh" 2>/dev/null
# 훅 등급: measurement (Phase 2-C 2026-04-19 세션73 timing 배선)
_HA_START=$(hook_timing_start)

HANDOFF="$PATH_HANDOFF"
ARCHIVE_DIR="$PROJECT_ROOT/98_아카이브"
LOCK_FILE="$PROJECT_ROOT/.claude/state/handoff_archive.lock"
COOLDOWN=300  # 5분

# stdin JSON에서 file_path 추출 — HANDOFF 변경이 아니면 즉시 종료
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | safe_json_get "file_path" 2>/dev/null || echo "$INPUT" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
if ! echo "$FILE_PATH" | grep -qi "HANDOFF"; then
  hook_timing_end "handoff_archive" "$_HA_START" "skip_nonhandoff"
  exit 0
fi

# 파일 존재 확인
if [ ! -f "$HANDOFF" ]; then
  hook_timing_end "handoff_archive" "$_HA_START" "skip_nofile"
  exit 0
fi

# 줄 수 확인 — 400줄 이하면 아카이브 불필요
LINE_COUNT=$(wc -l < "$HANDOFF" 2>/dev/null || echo 0)
if [ "$LINE_COUNT" -le 400 ]; then
  hook_timing_end "handoff_archive" "$_HA_START" "skip_under400"
  exit 0
fi

# 재귀 방지: lock/cooldown 확인
if [ -f "$LOCK_FILE" ]; then
  LOCK_EPOCH=$(stat -c '%Y' "$LOCK_FILE" 2>/dev/null || stat -f '%m' "$LOCK_FILE" 2>/dev/null || echo 0)
  NOW_EPOCH=$(date '+%s' 2>/dev/null || echo 999999999)
  ELAPSED=$(( NOW_EPOCH - LOCK_EPOCH ))
  if [ "$ELAPSED" -lt "$COOLDOWN" ]; then
    hook_timing_end "handoff_archive" "$_HA_START" "skip_cooldown"
    exit 0
  fi
fi

# lock 생성
mkdir -p "$(dirname "$LOCK_FILE")" 2>/dev/null
touch "$LOCK_FILE" 2>/dev/null

hook_log "handoff_archive" "trigger: ${LINE_COUNT} lines, archiving" 2>/dev/null || true

# 세션 헤더 위치 찾기 — "## 0." "## 1." 등
# 최신 2세션(## 0., ## 1.)의 끝 위치 = 세 번째 "## " 헤더 직전
THIRD_HEADER_LINE=""
HEADER_COUNT=0
while IFS= read -r line_num; do
  HEADER_COUNT=$((HEADER_COUNT + 1))
  if [ "$HEADER_COUNT" -eq 3 ]; then
    THIRD_HEADER_LINE="$line_num"
    break
  fi
done < <(grep -n '^## ' "$HANDOFF" | cut -d: -f1)

# 세션 헤더가 3개 미만이면 아카이브할 내용 없음
if [ -z "$THIRD_HEADER_LINE" ]; then
  rm -f "$LOCK_FILE" 2>/dev/null
  hook_timing_end "handoff_archive" "$_HA_START" "skip_noheaders"
  exit 0
fi

# 분리 지점: 세 번째 ## 헤더 직전까지 유지
KEEP_UNTIL=$((THIRD_HEADER_LINE - 1))

# 아카이브 날짜 범위 추출 (아카이브 대상의 첫/마지막 날짜)
ARCHIVE_CONTENT=$(tail -n +"$THIRD_HEADER_LINE" "$HANDOFF")
FIRST_DATE=$(echo "$ARCHIVE_CONTENT" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1)
LAST_DATE=$(echo "$ARCHIVE_CONTENT" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | tail -1)

if [ -z "$FIRST_DATE" ]; then
  FIRST_DATE=$(date '+%Y%m%d')
fi
if [ -z "$LAST_DATE" ]; then
  LAST_DATE="$FIRST_DATE"
fi

# 날짜 형식 변환 (YYYY-MM-DD → YYYYMMDD)
FIRST_DATE_COMPACT=$(echo "$FIRST_DATE" | tr -d '-')
LAST_DATE_COMPACT=$(echo "$LAST_DATE" | tr -d '-')

ARCHIVE_FILE="$ARCHIVE_DIR/handoff_archive_${LAST_DATE_COMPACT}_${FIRST_DATE_COMPACT}.md"

# 아카이브 파일이 이미 있으면 append
mkdir -p "$ARCHIVE_DIR" 2>/dev/null
if [ -f "$ARCHIVE_FILE" ]; then
  printf '\n---\n\n' >> "$ARCHIVE_FILE"
fi
echo "$ARCHIVE_CONTENT" >> "$ARCHIVE_FILE"

# HANDOFF.md 축소: 최신 2세션 + 공통 머리말 유지 + 아카이브 참조
KEPT_CONTENT=$(head -n "$KEEP_UNTIL" "$HANDOFF")
ARCHIVE_REF="> **이전 세션 이력 아카이브**: \`98_아카이브/$(basename "$ARCHIVE_FILE")\`"

# 기존 아카이브 참조 제거 후 새로 추가
KEPT_CONTENT=$(echo "$KEPT_CONTENT" | grep -v '이전 세션 이력 아카이브')

printf '%s\n\n%s\n' "$KEPT_CONTENT" "$ARCHIVE_REF" > "$HANDOFF"

NEW_LINE_COUNT=$(wc -l < "$HANDOFF" 2>/dev/null || echo 0)
hook_log "handoff_archive" "done: ${LINE_COUNT}→${NEW_LINE_COUNT} lines, archive=$(basename "$ARCHIVE_FILE")" 2>/dev/null || true

hook_timing_end "handoff_archive" "$_HA_START" "archived"
exit 0
