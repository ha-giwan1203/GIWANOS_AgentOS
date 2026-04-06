#!/bin/bash
# final_check.sh — 커밋 전 세션 마감 점검 (수동 실행, 자동 수정 금지)
# completion_gate(종료 차단)와 별개. 이 스크립트는 "사전 점검 + 요약"만 수행.
# GPT+Claude 합의 2026-04-07

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
HOOKS_DIR="$PROJECT_DIR/.claude/hooks"
FAIL=0

echo "=== Final Check (커밋 전 점검) ==="
echo ""

# 1. 공통 모듈 변경 시 호출부 전수 확인
echo "--- 1. 구 로그 직접 참조 잔존 확인 ---"
STALE=$(grep -rl 'hook_log\.txt' "$HOOKS_DIR"/*.sh 2>/dev/null | grep -v smoke_test.sh | grep -v final_check.sh)
if [ -n "$STALE" ]; then
  echo "  [FAIL] hook_log.txt 직접 참조 잔존: $STALE"
  FAIL=$((FAIL+1))
else
  echo "  [OK] hook_log.txt 직접 참조 0건"
fi

echo ""

# 2. smoke_test 실행
echo "--- 2. smoke_test 실행 ---"
bash "$HOOKS_DIR/smoke_test.sh"
if [ $? -ne 0 ]; then
  FAIL=$((FAIL+1))
fi

echo ""

# 3. 변경 파일 요약 (git show --stat 미리보기)
echo "--- 3. 미커밋 변경 파일 ---"
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

# 4. TASKS/HANDOFF 최신화 확인
echo "--- 4. TASKS/HANDOFF 갱신 확인 ---"
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

# === 결과 ===
if [ "$FAIL" -gt 0 ]; then
  echo "=== FAIL: $FAIL건 미해결. 커밋 전 확인 필요. ==="
  exit 1
else
  echo "=== ALL CLEAR. 커밋 가능. ==="
  exit 0
fi
