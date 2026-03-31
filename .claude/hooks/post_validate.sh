#!/bin/bash
# PostToolUse(Write|Edit|MultiEdit) hook — 파일 수정 후 자동 검증
# v2: CLAUDE.md 내부 모순 자동 감지 추가 (GPT 합의 2026-04-01)

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
ti = d.get('tool_input', {})
print(ti.get('file_path', ti.get('file', '')))
" 2>/dev/null)

HOOK_LOG="$HOME/Desktop/업무리스트/.claude/hooks/hook_log.txt"
echo "[Hook] PostToolUse: $(date '+%Y-%m-%d %H:%M:%S') | $FILE_PATH" >> "$HOOK_LOG"

# === TASKS.md 수정 시 ===
if echo "$FILE_PATH" | grep -q "TASKS.md"; then
  echo "[Hook] TASKS.md 수정 감지. 진행 중 항목 1개 이하 유지 확인 필요." >> "$HOOK_LOG"
fi

# === CLAUDE.md 수정 시 — 내부 모순 자동 감지 ===
if echo "$FILE_PATH" | grep -qi "CLAUDE.md"; then
  echo "[Hook] CLAUDE.md 수정 감지. 정합성 검사 시작." >> "$HOOK_LOG"

  # 1. timeout 값 불일치 검사 (같은 파일에서 다른 timeout 값)
  TIMEOUTS=$(grep -oE '[0-9]+초' "$FILE_PATH" 2>/dev/null | sort -u | wc -l)

  # 2. polling 간격 불일치 검사
  POLL_3=$(grep -c "3초" "$FILE_PATH" 2>/dev/null || echo 0)
  POLL_5=$(grep -c "5초\|sleep 5" "$FILE_PATH" 2>/dev/null || echo 0)
  POLL_OLD=$(grep -cE "10초 대기|15~30초|60초" "$FILE_PATH" 2>/dev/null || echo 0)

  # 3. find() 금지인데 find 참조 남아있는지
  HAS_FIND_BAN=$(grep -c "find().*금지\|find.*방식.*금지" "$FILE_PATH" 2>/dev/null || echo 0)
  HAS_FIND_USE=$(grep -c "find 순서로\|find()로" "$FILE_PATH" 2>/dev/null || echo 0)

  # 4. 참조 파일 존재 확인
  REFS=$(grep -oE '`[0-9A-Za-z_/가-힣.]+\.(md|sh|json)`' "$FILE_PATH" 2>/dev/null | tr -d '`' | sort -u)
  BASE_DIR=$(dirname "$FILE_PATH")
  PROJECT_ROOT="$HOME/Desktop/업무리스트"

  ISSUES=""

  if [ "$HAS_FIND_BAN" -gt 0 ] && [ "$HAS_FIND_USE" -gt 0 ]; then
    ISSUES="${ISSUES}[FAIL] find() 금지 규칙과 find 사용 참조가 동시에 존재\n"
  fi

  for ref in $REFS; do
    # 상대/절대 경로 모두 확인
    if [ ! -f "$BASE_DIR/$ref" ] && [ ! -f "$PROJECT_ROOT/$ref" ]; then
      ISSUES="${ISSUES}[WARN] 참조 파일 미존재: $ref\n"
    fi
  done

  if [ -n "$ISSUES" ]; then
    echo -e "[Hook] CLAUDE.md 정합성 검사 결과:\n$ISSUES" >> "$HOOK_LOG"
    # Claude에게 피드백 (stdout으로 additionalContext 전달)
    echo "{\"additionalContext\":\"[PostToolUse Hook] CLAUDE.md 정합성 문제 감지:\\n${ISSUES}수정 확인 필요.\"}"
  else
    echo "[Hook] CLAUDE.md 정합성 검사 PASS." >> "$HOOK_LOG"
  fi
fi
