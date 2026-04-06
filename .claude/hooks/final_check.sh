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

# 2. python3 잔존 참조 확인 (운영 훅 전용, auto_compile은 py_compile 필요로 제외)
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
# README 제목에서 "활성 Hook (N개" 추출, STATUS에서 "N개 등록" 추출
README_COUNT=$(grep -oP '활성 Hook \(\K\d+' "$HOOKS_DIR/README.md" 2>/dev/null || echo 0)
STATUS_COUNT=$(grep -oP '\K\d+(?=개 등록)' "$PROJECT_DIR/90_공통기준/업무관리/STATUS.md" 2>/dev/null | head -1 || echo 0)
SETTINGS_COUNT=$(grep -c '"\.claude/hooks/[a-z_]*\.sh"' "$PROJECT_DIR/.claude/settings.local.json" 2>/dev/null || echo 0)
echo "  README 테이블: ${README_COUNT}개 / STATUS 기재: ${STATUS_COUNT}개 / settings 등록: ${SETTINGS_COUNT}개"
if [ "$README_COUNT" -ne "$STATUS_COUNT" ] 2>/dev/null; then
  echo "  [WARN] README($README_COUNT) ≠ STATUS($STATUS_COUNT) — hook 개수 불일치"
  FAIL=$((FAIL+1))
else
  echo "  [OK] README-STATUS hook 개수 일치"
fi

echo ""

# 4. HANDOFF '구현 예정' vs 실제 코드 교차확인 (cp 차단 등)
echo "--- 4. HANDOFF 계획 vs 실물 교차확인 ---"
if grep -q 'cp' "$HOOKS_DIR/block_dangerous.sh" 2>/dev/null; then
  echo "  [OK] block_dangerous DANGER_CMDS에 cp 포함"
else
  echo "  [WARN] block_dangerous DANGER_CMDS에 cp 누락 (HANDOFF 기재와 불일치)"
  FAIL=$((FAIL+1))
fi

echo ""

# 5. smoke_test 실행
echo "--- 5. smoke_test 실행 ---"
bash "$HOOKS_DIR/smoke_test.sh"
if [ $? -ne 0 ]; then
  FAIL=$((FAIL+1))
fi

echo ""

# 6. 변경 파일 요약 (git show --stat 미리보기)
echo "--- 6. 미커밋 변경 파일 ---"
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

# 7. TASKS/HANDOFF 최신화 확인
echo "--- 7. TASKS/HANDOFF 갱신 확인 ---"
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
