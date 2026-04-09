#!/bin/bash
# final_check.sh — 커밋 전 자체검증 (commit_gate에서 자동 호출)
# --fast: 교차검증만 (매 커밋/푸시), --full: fast + smoke_test (hook/settings 변경 시)
# 기본값: --full (수동 실행 시)
# GPT+Claude 합의 2026-04-07

MODE="${1:---full}"
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
HOOKS_DIR="$PROJECT_DIR/.claude/hooks"
export CLAUDE_PROJECT_DIR="$PROJECT_DIR"
source "$HOOKS_DIR/hook_common.sh" 2>/dev/null || true
FAIL=0
WARN=0

warn() {
  echo "  [WARN] $1"
  WARN=$((WARN+1))
}

fail() {
  echo "  [FAIL] $1"
  FAIL=$((FAIL+1))
}

echo "=== Final Check ($MODE) ==="
echo ""

# === FAST 구간: 교차검증 (매 커밋 필수) ===

# 1. 구 로그 직접 참조 잔존 확인
echo "--- 1. 구 로그 직접 참조 잔존 확인 ---"
STALE=$(grep -rl 'hook_log\.txt' "$HOOKS_DIR"/*.sh 2>/dev/null | grep -v smoke_test.sh | grep -v final_check.sh)
if [ -n "$STALE" ]; then
  echo "  [FAIL] hook_log.txt 직접 참조 잔존: $STALE"
  FAIL=$((FAIL+1))
else
  echo "  [OK] hook_log.txt 직접 참조 0건"
fi
echo ""

# 2. python3 잔존 참조 확인
echo "--- 2. python3 잔존 참조 확인 ---"
PY3_REFS=$(grep -l 'python3 -c\|python3 -' "$HOOKS_DIR"/*.sh 2>/dev/null | grep -v smoke_test.sh | grep -v final_check.sh | grep -v auto_compile.sh | grep -v _archive)
if [ -n "$PY3_REFS" ]; then
  warn "python3 의존 잔존:"
  echo "$PY3_REFS" | while read f; do echo "    - $(basename $f)"; done
else
  echo "  [OK] 운영 훅 python3 의존 0건 (auto_compile 제외)"
fi
echo ""

# 3. 문서 간 hook 개수 정합성 확인
echo "--- 3. hook 개수 정합성 ---"
README_COUNT=$(sed -n 's/.*활성 Hook (\([0-9]*\)개.*/\1/p' "$HOOKS_DIR/README.md" 2>/dev/null | head -1)
README_COUNT=${README_COUNT:-0}
STATUS_COUNT=$(sed -n 's/.*| hooks 체계 | \([0-9]*\)개 등록.*/\1/p' "$PROJECT_DIR/90_공통기준/업무관리/STATUS.md" 2>/dev/null | head -1)
STATUS_COUNT=${STATUS_COUNT:-0}
echo "  README: ${README_COUNT}개 / STATUS: ${STATUS_COUNT}개"
if [ "$README_COUNT" -ne "$STATUS_COUNT" ] 2>/dev/null; then
  warn "README($README_COUNT) ≠ STATUS($STATUS_COUNT) — hook 개수 불일치"
else
  echo "  [OK] README-STATUS hook 개수 일치"
fi
echo ""

# 4. HANDOFF 계획 vs 실물 교차확인
echo "--- 4. HANDOFF 계획 vs 실물 교차확인 ---"
if grep -q 'cp' "$HOOKS_DIR/block_dangerous.sh" 2>/dev/null; then
  echo "  [OK] block_dangerous DANGER_CMDS에 cp 포함"
else
  warn "block_dangerous DANGER_CMDS에 cp 누락"
fi
echo ""

# 5. settings.local.json vs README hook 개수 대조
echo "--- 5. settings.local hook 개수 대조 ---"
SETTINGS="$PROJECT_DIR/.claude/settings.local.json"
if [ -f "$SETTINGS" ]; then
  # helper 제외 (hook_common, smoke_test, final_check는 훅이 아닌 유틸)
  SETTINGS_HOOKS=$(grep -o '[a-z_]*\.sh' "$SETTINGS" 2>/dev/null | sort -u | grep -v hook_common | grep -v smoke_test | grep -v final_check | wc -l)
  echo "  settings.local: ${SETTINGS_HOOKS}개 / README: ${README_COUNT}개"
  if [ "$SETTINGS_HOOKS" -ne "$README_COUNT" ] 2>/dev/null; then
    warn "settings.local($SETTINGS_HOOKS) ≠ README($README_COUNT)"
  else
    echo "  [OK] settings.local-README hook 개수 일치"
  fi
else
  warn "settings.local.json 파일 없음"
fi
echo ""

# 6. 상태 문서 3종 날짜 동기화 확인 (staged 우선, 없으면 working tree)
echo "--- 6. TASKS/HANDOFF/STATUS 날짜 동기화 ---"
STATUS_FILE="$PROJECT_DIR/90_공통기준/업무관리/STATUS.md"
TASKS="$PROJECT_DIR/90_공통기준/업무관리/TASKS.md"
HANDOFF="$PROJECT_DIR/90_공통기준/업무관리/HANDOFF.md"

# staged snapshot에서 날짜 추출 시도, 없으면 working tree fallback
_get_date() {
  local rel_path="$1"
  local staged_content
  staged_content=$(cd "$PROJECT_DIR" && git show :"$rel_path" 2>/dev/null)
  if [ -n "$staged_content" ]; then
    echo "$staged_content" | sed -n 's/.*최종 업데이트: \([0-9-]*\).*/\1/p' | head -1
  else
    sed -n 's/.*최종 업데이트: \([0-9-]*\).*/\1/p' "$PROJECT_DIR/$rel_path" 2>/dev/null | head -1
  fi
}

TASKS_DATE=$(_get_date "90_공통기준/업무관리/TASKS.md")
HANDOFF_DATE=$(_get_date "90_공통기준/업무관리/HANDOFF.md")
STATUS_DATE=$(_get_date "90_공통기준/업무관리/STATUS.md")
echo "  TASKS: $TASKS_DATE / HANDOFF: $HANDOFF_DATE / STATUS: $STATUS_DATE"

if [ -n "$TASKS_DATE" ] && [ -n "$STATUS_DATE" ]; then
  if [[ "$STATUS_DATE" < "$TASKS_DATE" ]]; then
    warn "STATUS($STATUS_DATE) < TASKS($TASKS_DATE) — STATUS.md 드리프트"
  else
    echo "  [OK] STATUS 날짜 >= TASKS 날짜"
  fi
fi
if [ -n "$TASKS_DATE" ] && [ -n "$HANDOFF_DATE" ]; then
  if [[ "$HANDOFF_DATE" < "$TASKS_DATE" ]]; then
    warn "HANDOFF($HANDOFF_DATE) < TASKS($TASKS_DATE) — HANDOFF 드리프트"
  else
    echo "  [OK] HANDOFF 날짜 >= TASKS 날짜"
  fi
fi
echo ""

# 7. TASKS/HANDOFF 최신화 확인
echo "--- 7. TASKS/HANDOFF 갱신 확인 ---"
STATE_DIR="$PROJECT_DIR/90_공통기준/agent-control/state"
MARKER="$STATE_DIR/write_marker.flag"

if [ -f "$MARKER" ]; then
  MARKER_EPOCH=$(file_mtime "$MARKER")
  for F in "$TASKS" "$HANDOFF"; do
    NAME=$(basename "$F")
    if [ -f "$F" ]; then
      F_EPOCH=$(file_mtime "$F")
      if [ "$F_EPOCH" -lt "$MARKER_EPOCH" ] 2>/dev/null; then
        fail "$NAME — write_marker 이후 미갱신"
      else
        echo "  [OK] $NAME 갱신됨"
      fi
    else
      fail "$NAME 파일 없음"
    fi
  done
else
  echo "  [INFO] write_marker 없음 (파일 변경 없는 세션)"
fi
echo ""

# === FULL 구간: smoke_test (--full 시에만) ===

if [ "$MODE" = "--full" ]; then
  echo "--- 8. smoke_test 실행 ---"
  bash "$HOOKS_DIR/smoke_test.sh"
  if [ $? -ne 0 ]; then
    FAIL=$((FAIL+1))
  fi
  echo ""

  echo "--- 9. 미커밋 변경 파일 ---"
  CHANGES=$(git_relevant_change_list)
  if [ -z "$CHANGES" ]; then
    echo "  [INFO] 변경 파일 없음"
  else
    echo "$CHANGES" | sort -u | while read f; do
      [ -n "$f" ] && echo "  - $f"
    done
  fi
  echo ""
fi

# === 결과 ===
if [ "$FAIL" -gt 0 ]; then
  echo "=== FAIL: $FAIL건 미해결 / WARN: $WARN건. ==="
  exit 1
elif [ "$WARN" -gt 0 ]; then
  echo "=== WARN: $WARN건 경고. 커밋은 허용되지만 확인 권장. ==="
  exit 0
else
  echo "=== ALL CLEAR. ==="
  exit 0
fi
