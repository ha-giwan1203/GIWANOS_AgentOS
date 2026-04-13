#!/bin/bash
# E2E Hook Tests — 실제 입출력 검증 (Phase 3-2)
# smoke_test.sh(정적 구조)와 분리. smoke_test.sh --with-e2e로 연결 가능.
# 10개 시나리오: block_dangerous(2) + protect_files(2) + session_start(3) + evidence_gate(3)

export LC_ALL=en_US.UTF-8

PASS=0
FAIL=0
TOTAL=0
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
HOOKS_DIR="$PROJECT_DIR/.claude/hooks"

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

echo "=== E2E Hook Tests ==="
echo ""

# --- 1. block_dangerous: deny ---
echo "--- E2E-1. block_dangerous: rm -rf / → deny ---"
RESULT=$(echo '{"command":"rm -rf /"}' | bash "$HOOKS_DIR/block_dangerous.sh" 2>/dev/null)
echo "$RESULT" | grep -q '"decision":"deny"'
check $? "block_dangerous: rm -rf / → deny"

# --- 2. block_dangerous: safe command → no deny ---
echo "--- E2E-2. block_dangerous: ls → pass ---"
RESULT=$(echo '{"command":"ls -la"}' | bash "$HOOKS_DIR/block_dangerous.sh" 2>/dev/null)
# 안전한 명령은 출력 없이 exit 0
test -z "$RESULT" || ! echo "$RESULT" | grep -q '"decision":"deny"'
check $? "block_dangerous: ls → no deny"

# --- 3. protect_files: xlsx → deny ---
echo "--- E2E-3. protect_files: test.xlsx → deny ---"
RESULT=$(echo '{"file_path":"test.xlsx"}' | bash "$HOOKS_DIR/protect_files.sh" 2>/dev/null)
echo "$RESULT" | grep -q '"decision":"deny"'
check $? "protect_files: xlsx → deny"

# --- 4. protect_files: .sh → pass ---
echo "--- E2E-4. protect_files: test.sh → pass ---"
RESULT=$(echo '{"file_path":"test.sh"}' | bash "$HOOKS_DIR/protect_files.sh" 2>/dev/null)
test -z "$RESULT" || ! echo "$RESULT" | grep -q '"decision":"deny"'
check $? "protect_files: .sh → no deny"

# --- 5. session_start_restore: fresh kernel ---
echo "--- E2E-5. session_start: fresh kernel → TASKS 출력 ---"
STATE_DIR="$PROJECT_DIR/.claude/state"
KERNEL="$STATE_DIR/session_kernel.md"
KERNEL_BACKUP=""
# 백업 + fresh kernel 생성
if [ -f "$KERNEL" ]; then
  KERNEL_BACKUP="${KERNEL}.e2e_bak"
  cp "$KERNEL" "$KERNEL_BACKUP"
fi
mkdir -p "$STATE_DIR"
echo "# Test Kernel" > "$KERNEL"
touch "$KERNEL"  # ensure fresh mtime
RESULT=$(echo '{"source":"e2e_test"}' | bash "$HOOKS_DIR/session_start_restore.sh" 2>/dev/null)
echo "$RESULT" | grep -q "TASKS"
check $? "session_start: fresh kernel → TASKS 출력"

# --- 6. session_start_restore: stale kernel ---
echo "--- E2E-6. session_start: stale kernel → fallback ---"
# 48시간 전 타임스탬프로 설정
touch -t "$(date -d '48 hours ago' '+%Y%m%d%H%M.%S' 2>/dev/null || date -v-48H '+%Y%m%d%H%M.%S' 2>/dev/null)" "$KERNEL" 2>/dev/null
# Windows Git Bash: touch -t가 안 되면 fallback
if [ $? -ne 0 ]; then
  # 25시간 = 90000초 전으로 근사
  python -c "import os,time; os.utime('$KERNEL',(time.time()-90000,time.time()-90000))" 2>/dev/null
fi
RESULT=$(echo '{"source":"e2e_test"}' | bash "$HOOKS_DIR/session_start_restore.sh" 2>/dev/null)
echo "$RESULT" | grep -qi "stale\|fallback"
check $? "session_start: stale kernel → stale/fallback 메시지"

# --- 7. session_start_restore: missing kernel ---
echo "--- E2E-7. session_start: missing kernel → fallback ---"
rm -f "$KERNEL"
RESULT=$(echo '{"source":"e2e_test"}' | bash "$HOOKS_DIR/session_start_restore.sh" 2>/dev/null)
echo "$RESULT" | grep -qi "없음\|fallback"
check $? "session_start: missing kernel → 없음/fallback 메시지"

# kernel 복원
if [ -n "$KERNEL_BACKUP" ] && [ -f "$KERNEL_BACKUP" ]; then
  mv "$KERNEL_BACKUP" "$KERNEL"
elif [ ! -f "$KERNEL" ]; then
  # 원래 없었으면 삭제 상태 유지
  :
fi

# --- 8~10. evidence_gate 테스트 ---
# evidence_init은 session_key(sha1(CLAUDE_TRANSCRIPT_PATH))로 디렉토리 결정
# 테스트용 transcript path 설정 → 해당 해시 디렉토리에 .req 생성
E2E_TRANSCRIPT="e2e_test_$$"
E2E_SK=$(printf '%s' "$E2E_TRANSCRIPT" | sha1sum 2>/dev/null | awk '{print $1}')
if [ -z "$E2E_SK" ]; then
  E2E_SK=$(printf '%s' "$E2E_TRANSCRIPT" | shasum 2>/dev/null | awk '{print $1}')
fi
E2E_EV_DIR="$PROJECT_DIR/.claude/state/evidence/$E2E_SK"
E2E_REQ_DIR="$E2E_EV_DIR/requires"
mkdir -p "$E2E_REQ_DIR" "$E2E_EV_DIR/proofs"
touch "$E2E_EV_DIR/.session_start"
# .session_start를 과거로 설정해 .req가 newer로 판정되도록
sleep 1

# --- 8. evidence_gate: no-req → 완전 통과 ---
echo "--- E2E-8. evidence_gate: no-req → pass ---"
RESULT=$(CLAUDE_TRANSCRIPT_PATH="$E2E_TRANSCRIPT" bash "$HOOKS_DIR/evidence_gate.sh" <<< '{"command":"ls"}' 2>/dev/null)
test -z "$RESULT" || ! echo "$RESULT" | grep -q '"decision":"deny"'
check $? "evidence_gate: no-req → pass"

# --- 9. evidence_gate: map_scope.req + Write → deny ---
echo "--- E2E-9. evidence_gate: map_scope.req + Write → deny ---"
touch "$E2E_REQ_DIR/map_scope.req"
RESULT=$(CLAUDE_TRANSCRIPT_PATH="$E2E_TRANSCRIPT" bash "$HOOKS_DIR/evidence_gate.sh" <<< '{"command":"","tool_name":"Write","tool_input":"some file"}' 2>/dev/null)
echo "$RESULT" | grep -q '"decision":"deny"'
check $? "evidence_gate: map_scope + Write → deny"

# --- 10. evidence_gate: tasks_handoff.req + git commit → deny ---
echo "--- E2E-10. evidence_gate: tasks_handoff.req + git commit → deny ---"
touch "$E2E_REQ_DIR/tasks_handoff.req"
RESULT=$(CLAUDE_TRANSCRIPT_PATH="$E2E_TRANSCRIPT" bash "$HOOKS_DIR/evidence_gate.sh" <<< '{"command":"git commit -m test"}' 2>/dev/null)
echo "$RESULT" | grep -q '"decision":"deny"'
check $? "evidence_gate: tasks_handoff + git commit → deny"

# 임시 evidence 정리
rm -rf "$E2E_EV_DIR"

echo ""
echo "=== E2E 결과: $PASS/$TOTAL PASS, $FAIL FAIL ==="
if [ "$FAIL" -gt 0 ]; then
  echo "FAIL 있음."
  exit 1
else
  echo "ALL PASS."
  exit 0
fi
