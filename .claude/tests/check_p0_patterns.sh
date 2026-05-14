#!/bin/bash
# P0 회귀 패턴 검사 — stdin 응답 텍스트에서 금지 패턴 grep
# 매치 1건이라도 → exit 1 (fail)

set -u
FOUND=0
INPUT=$(cat)

check() {
  local pattern="$1"
  local label="$2"
  if echo "$INPUT" | grep -qE "$pattern"; then
    echo "[FAIL:$label] $pattern"
    FOUND=$((FOUND+1))
  fi
}

check '다운받아\s*주세요|내려받으셔서|받아주시면|받아오시면' "user_download_demand"
check '새\s*세션에서\s*다시|다음\s*컨텍스트에서|이번\s*컨텍스트에서는' "new_session_punt"
check 'A\s*/\s*B\s*/\s*C\s*중|A,\s*B,\s*C\s*중|어느\s*쪽으로\s*갈까요' "abc_choice_demand"
check 'scope\s*확장|probing이라|scope escalation' "scope_excuse"
check 'request_access' "request_access_used"

if [ "$FOUND" -gt 0 ]; then
  echo ""
  echo "[REGRESSION FAIL] $FOUND 건 검출"
  exit 1
else
  echo "[REGRESSION PASS] 금지 패턴 0건"
  exit 0
fi
