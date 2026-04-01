#!/bin/bash
# Hooks Smoke Test — hooks 수정 후 반드시 실행
# 4묶음 10개 테스트 케이스

PASS=0
FAIL=0
TOTAL=0
LOG="$HOME/Desktop/업무리스트/.claude/hooks/hook_log.txt"
HOOKS_DIR="$HOME/Desktop/업무리스트/.claude/hooks"

check() {
  TOTAL=$((TOTAL+1))
  if [ "$1" = "0" ]; then
    PASS=$((PASS+1))
    echo "  [PASS] $2"
  else
    FAIL=$((FAIL+1))
    echo "  [FAIL] $2"
  fi
}

echo "=== Hooks Smoke Test ==="
echo ""

# === 1. Stop Guard ===
echo "--- 1. Stop Guard (stop_guard.sh) ---"

# 1-1. 스크립트 존재 + 실행 가능
test -x "$HOOKS_DIR/stop_guard.sh"
check $? "stop_guard.sh 존재 + 실행 가능"

# 1-2. 금지 문구 패턴 7개 정의 확인
COUNT=$(grep -c 'FORBIDDEN_PATTERNS' "$HOOKS_DIR/stop_guard.sh" 2>/dev/null)
test "$COUNT" -gt 0
check $? "금지 문구 패턴 배열 정의됨"

# 1-3. BLOCK 로깅 코드 존재
grep -q 'stop_guard BLOCK' "$HOOKS_DIR/stop_guard.sh"
check $? "BLOCK 시 hook_log.txt 로깅 코드 존재"

# 1-4. python3 파싱 코드 존재 (마지막 assistant 블록 추출)
grep -q 'python3' "$HOOKS_DIR/stop_guard.sh"
check $? "python3 transcript 파싱 코드 존재"

echo ""

# === 2. UserPromptSubmit (prompt_inject.sh) ===
echo "--- 2. UserPromptSubmit (prompt_inject.sh) ---"

# 2-1. 스크립트 존재 + 실행 가능
test -x "$HOOKS_DIR/prompt_inject.sh"
check $? "prompt_inject.sh 존재 + 실행 가능"

# 2-2. 토론모드 키워드 감지 패턴 존재
grep -q '토론모드\|debate-mode\|공동작업' "$HOOKS_DIR/prompt_inject.sh"
check $? "토론모드/공동작업 키워드 감지 패턴 존재"

echo ""

# === 3. PostToolUse (post_validate.sh) ===
echo "--- 3. PostToolUse (post_validate.sh) ---"

# 3-1. 스크립트 존재 + 실행 가능
test -x "$HOOKS_DIR/post_validate.sh"
check $? "post_validate.sh 존재 + 실행 가능"

# 3-2. find() 충돌 감지 코드 존재
grep -q 'HAS_FIND_BAN\|HAS_FIND_USE' "$HOOKS_DIR/post_validate.sh"
check $? "find() 금지/사용 충돌 감지 코드 존재"

# 3-3. polling 불일치 감지 코드 존재
grep -q 'POLL_OLD' "$HOOKS_DIR/post_validate.sh"
check $? "구버전 polling 참조 감지 코드 존재"

echo ""

# === 4. SessionStart (session_start.sh) ===
echo "--- 4. SessionStart (session_start.sh) ---"

# 4-1. 스크립트 존재 + 실행 가능
test -x "$HOOKS_DIR/session_start.sh"
check $? "session_start.sh 존재 + 실행 가능"

echo ""

# === 5. Pre Write Guard (pre_write_guard.sh) ===
echo "--- 5. Pre Write Guard (pre_write_guard.sh) ---"

test -x "$HOOKS_DIR/pre_write_guard.sh"
check $? "pre_write_guard.sh 존재 + 실행 가능"

grep -q 'EXEMPT_SUFFIXES' "$HOOKS_DIR/pre_write_guard.sh"
check $? "EXEMPT 파일 목록 정의됨"

grep -q 'parse_plan' "$HOOKS_DIR/pre_write_guard.sh"
check $? "plan.md 파싱 로직 존재"

echo ""

# === 6. Post Write Dirty (post_write_dirty.sh) ===
echo "--- 6. Post Write Dirty (post_write_dirty.sh) ---"

test -x "$HOOKS_DIR/post_write_dirty.sh"
check $? "post_write_dirty.sh 존재 + 실행 가능"

grep -q 'dirty.flag' "$HOOKS_DIR/post_write_dirty.sh"
check $? "dirty.flag 생성 로직 존재"

echo ""

# === 7. Pre Finish Guard (pre_finish_guard.sh) ===
echo "--- 7. Pre Finish Guard (pre_finish_guard.sh) ---"

test -x "$HOOKS_DIR/pre_finish_guard.sh"
check $? "pre_finish_guard.sh 존재 + 실행 가능"

grep -q 'verify.json' "$HOOKS_DIR/pre_finish_guard.sh"
check $? "verify.json 검사 로직 존재"

echo ""

# === 8. GPT Followup Guard (gpt_followup_guard.sh) ===
echo "--- 8. GPT Followup Guard (gpt_followup_guard.sh) ---"

test -x "$HOOKS_DIR/gpt_followup_guard.sh"
check $? "gpt_followup_guard.sh 존재 + 실행 가능"

grep -q 'pending.flag\|pending_flag' "$HOOKS_DIR/gpt_followup_guard.sh"
check $? "pending.flag 상태기계 로직 존재"

echo ""

# === 결과 ===
echo "=== 결과: $PASS/$TOTAL PASS, $FAIL FAIL ==="
if [ "$FAIL" -gt 0 ]; then
  echo "WARNING: $FAIL개 실패. hooks 수정 확인 필요."
  exit 1
else
  echo "ALL PASS."
  exit 0
fi
