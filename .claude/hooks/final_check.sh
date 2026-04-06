#!/bin/bash
# final_check.sh — 커밋 전 자체검증 (commit_gate에서 자동 호출)
# --fast: 교차검증만 (매 커밋/푸시), --full: fast + smoke_test (hook/settings 변경 시)
# 기본값: --full (수동 실행 시)
# GPT+Claude 합의 2026-04-07

MODE="${1:---full}"
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
HOOKS_DIR="$PROJECT_DIR/.claude/hooks"
FAIL=0

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
  echo "  [WARN] python3 의존 잔존:"
  echo "$PY3_REFS" | while read f; do echo "    - $(basename $f)"; done
  FAIL=$((FAIL+1))
else
  echo "  [OK] 운영 훅 python3 의존 0건 (auto_compile 제외)"
fi
echo ""

# 3. 문서 간 hook 개수 정합성 확인
echo "--- 3. hook 개수 정합성 ---"
README_COUNT=$(grep -oP '활성 Hook \(\K\d+' "$HOOKS_DIR/README.md" 2>/dev/null || echo 0)
STATUS_COUNT=$(grep -oP '\K\d+(?=개 등록)' "$PROJECT_DIR/90_공통기준/업무관리/STATUS.md" 2>/dev/null | head -1 || echo 0)
echo "  README: ${README_COUNT}개 / STATUS: ${STATUS_COUNT}개"
if [ "$README_COUNT" -ne "$STATUS_COUNT" ] 2>/dev/null; then
  echo "  [WARN] README($README_COUNT) ≠ STATUS($STATUS_COUNT) — hook 개수 불일치"
  FAIL=$((FAIL+1))
else
  echo "  [OK] README-STATUS hook 개수 일치"
fi
echo ""

# 4. HANDOFF 계획 vs 실물 교차확인
echo "--- 4. HANDOFF 계획 vs 실물 교차확인 ---"
if grep -q 'cp' "$HOOKS_DIR/block_dangerous.sh" 2>/dev/null; then
  echo "  [OK] block_dangerous DANGER_CMDS에 cp 포함"
else
  echo "  [WARN] block_dangerous DANGER_CMDS에 cp 누락"
  FAIL=$((FAIL+1))
fi
echo ""

# 5. TASKS/HANDOFF 최신화 확인
echo "--- 5. TASKS/HANDOFF 갱신 확인 ---"
TASKS="$PROJECT_DIR/90_공통기준/업무관리/TASKS.md"
HANDOFF="$PROJECT_DIR/90_공통기준/업무관리/HANDOFF.md"
STATE_DIR="$PROJECT_DIR/90_공통기준/agent-control/state"
MARKER="$STATE_DIR/write_marker.flag"

if [ -f "$MARKER" ]; then
  MARKER_EPOCH=$(stat --format=%Y "$MARKER" 2>/dev/null || stat -f %m "$MARKER" 2>/dev/null || echo 0)
  for F in "$TASKS" "$HANDOFF"; do
    NAME=$(basename "$F")
    if [ -f "$F" ]; then
      F_EPOCH=$(stat --format=%Y "$F" 2>/dev/null || stat -f %m "$F" 2>/dev/null || echo 0)
      if [ "$F_EPOCH" -lt "$MARKER_EPOCH" ] 2>/dev/null; then
        echo "  [WARN] $NAME — write_marker 이후 미갱신"
        FAIL=$((FAIL+1))
      else
        echo "  [OK] $NAME 갱신됨"
      fi
    else
      echo "  [WARN] $NAME 파일 없음"
      FAIL=$((FAIL+1))
    fi
  done
else
  echo "  [INFO] write_marker 없음 (파일 변경 없는 세션)"
fi
echo ""

# === FULL 구간: smoke_test (--full 시에만) ===

if [ "$MODE" = "--full" ]; then
  echo "--- 6. smoke_test 실행 ---"
  bash "$HOOKS_DIR/smoke_test.sh"
  if [ $? -ne 0 ]; then
    FAIL=$((FAIL+1))
  fi
  echo ""

  echo "--- 7. 미커밋 변경 파일 ---"
  CHANGES=$(cd "$PROJECT_DIR" && git diff --name-only 2>/dev/null)
  STAGED=$(cd "$PROJECT_DIR" && git diff --cached --name-only 2>/dev/null)
  if [ -z "$CHANGES" ] && [ -z "$STAGED" ]; then
    echo "  [INFO] 변경 파일 없음"
  else
    echo "$CHANGES" "$STAGED" | sort -u | while read f; do
      [ -n "$f" ] && echo "  - $f"
    done
  fi
  echo ""
fi

# === 결과 ===
if [ "$FAIL" -gt 0 ]; then
  echo "=== FAIL: $FAIL건 미해결. ==="
  exit 1
else
  echo "=== ALL CLEAR. ==="
  exit 0
fi
