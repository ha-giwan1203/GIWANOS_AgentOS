#!/bin/bash
# nightly_capability_check.sh — 세션77 Round 2 Silent Failure 방지 (Gemini 최우선 안전망)
#
# 목적:
#   capability 테스트(smoke_test 167 케이스)를 일일 배치로 강제 실행하여 Silent Failure 조기 감지.
#   Round 2 Step 2에서 commit 경로 SMOKE_LEVEL=fast 기본값으로 capability가 commit 시 실행되지 않음.
#   이 스크립트가 매일 1회 전수 검증하여 "조용히 고장난 채 방치" 방지.
#
# 등급: measurement + advisory
#   - 실패 감지 시 incident 기록 + exit 2 (상위 알림 유도)
#   - 성공 시 .claude/state/nightly_capability_log.jsonl 기록 (관찰 이력)
#
# 사용법:
#   bash .claude/hooks/nightly_capability_check.sh            # 수동 실행
#   SMOKE_TEST_FORCE=1 자동 설정됨 (캐시 무시 강제 실행)
#
# Windows schtasks 등록 예시 (수동 1회):
#   schtasks /Create /TN "claude_nightly_capability" \
#     /TR "'C:\Program Files\Git\bin\bash.exe' -lc 'cd /c/Users/User/Desktop/업무리스트 && bash .claude/hooks/nightly_capability_check.sh'" \
#     /SC DAILY /ST 02:00 /F
#
# 등록 해제:
#   schtasks /Delete /TN "claude_nightly_capability" /F

set -u

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
HOOKS_DIR="$PROJECT_DIR/.claude/hooks"
STATE_DIR="$PROJECT_DIR/.claude/state"
LOG_FILE="$STATE_DIR/nightly_capability_log.jsonl"
LAST_OUTPUT="$STATE_DIR/nightly_capability_last_output.txt"

mkdir -p "$STATE_DIR" 2>/dev/null || true

START_TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
START_EPOCH=$(date +%s)

# 캐시 무시 강제 실행
export SMOKE_TEST_FORCE=1

bash "$HOOKS_DIR/smoke_test.sh" > "$LAST_OUTPUT" 2>&1
EXIT_CODE=$?

END_EPOCH=$(date +%s)
DURATION=$((END_EPOCH - START_EPOCH))

# 결과 파싱 (예: "=== 결과: 167/167 PASS, 0 FAIL ===")
RESULT_LINE=$(grep -E '^=== 결과' "$LAST_OUTPUT" | tail -1)
PASS_COUNT=$(echo "$RESULT_LINE" | grep -oE '[0-9]+/[0-9]+' | head -1 | cut -d'/' -f1)
TOTAL_COUNT=$(echo "$RESULT_LINE" | grep -oE '[0-9]+/[0-9]+' | head -1 | cut -d'/' -f2)
FAIL_COUNT=$(echo "$RESULT_LINE" | sed -n 's/.*,\s*\([0-9]\+\)\s*FAIL.*/\1/p' | head -1)
[ -z "${PASS_COUNT:-}" ] && PASS_COUNT=null
[ -z "${TOTAL_COUNT:-}" ] && TOTAL_COUNT=null
[ -z "${FAIL_COUNT:-}" ] && FAIL_COUNT=0

# jsonl append
printf '{"ts":"%s","duration_sec":%d,"exit_code":%d,"pass":%s,"total":%s,"fail":%s,"source":"nightly_capability_check"}\n' \
  "$START_TS" "$DURATION" "$EXIT_CODE" "$PASS_COUNT" "$TOTAL_COUNT" "$FAIL_COUNT" >> "$LOG_FILE"

# FAIL 발생 시 incident 기록
if [ "$EXIT_CODE" -ne 0 ]; then
  if [ -f "$HOOKS_DIR/hook_common.sh" ]; then
    # shellcheck disable=SC1091
    source "$HOOKS_DIR/hook_common.sh" 2>/dev/null || true
    if declare -f hook_incident > /dev/null; then
      hook_incident "silent_failure" "nightly_capability_check" "" \
        "smoke_test --full FAIL ($FAIL_COUNT 건)" \
        "\"classification_reason\":\"silent_failure\",\"source\":\"nightly_capability_check\",\"duration_sec\":$DURATION" \
        2>/dev/null || true
    fi
  fi
  echo "[FAIL] capability 테스트 ${FAIL_COUNT}건 실패 감지 — incident 기록됨" >&2
  echo "  최근 출력: $LAST_OUTPUT" >&2
  exit 2
fi

echo "[OK] capability 테스트 ${PASS_COUNT}/${TOTAL_COUNT} PASS (${DURATION}초)"
exit 0
