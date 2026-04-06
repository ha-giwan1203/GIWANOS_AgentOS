#!/bin/bash
# Hooks Smoke Test v2 — 현행 훅 실물 기준 (2026-04-07)
# 운영 훅 11개 + hook_common + incident_ledger 검증

PASS=0
FAIL=0
TOTAL=0
HOOKS_DIR="$HOME/Desktop/업무리스트/.claude/hooks"
PROJECT_DIR="$HOME/Desktop/업무리스트"

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

echo "=== Hooks Smoke Test v2 ==="
echo ""

# === 1. hook_common.sh ===
echo "--- 1. hook_common.sh (공통 로깅) ---"
test -f "$HOOKS_DIR/hook_common.sh"
check $? "hook_common.sh 존재"

grep -q 'hook_log()' "$HOOKS_DIR/hook_common.sh"
check $? "hook_log() 함수 정의됨"

grep -q 'hook_incident()' "$HOOKS_DIR/hook_common.sh"
check $? "hook_incident() 함수 정의됨"

grep -q 'hook_log.jsonl' "$HOOKS_DIR/hook_common.sh"
check $? "로그 파일명 hook_log.jsonl (JSON 형식)"

grep -q '_rotate_file()' "$HOOKS_DIR/hook_common.sh"
check $? "로테이션 함수 _rotate_file() 정의됨"

echo ""

# === 2. block_dangerous.sh (PreToolUse/Bash) ===
echo "--- 2. block_dangerous.sh ---"
test -x "$HOOKS_DIR/block_dangerous.sh"
check $? "block_dangerous.sh 존재 + 실행 가능"

grep -q 'hook_common.sh' "$HOOKS_DIR/block_dangerous.sh"
check $? "hook_common.sh source 연결"

grep -q 'rm -rf' "$HOOKS_DIR/block_dangerous.sh"
check $? "파괴 명령 차단 패턴 존재"

echo ""

# === 3. protect_files.sh (PreToolUse/Write|Edit) ===
echo "--- 3. protect_files.sh ---"
test -x "$HOOKS_DIR/protect_files.sh"
check $? "protect_files.sh 존재 + 실행 가능"

grep -q 'deny\|ask' "$HOOKS_DIR/protect_files.sh"
check $? "2계층 판정 (deny/ask) 로직 존재"

echo ""

# === 4. send_gate.sh (PreToolUse/javascript_tool) ===
echo "--- 4. send_gate.sh ---"
test -x "$HOOKS_DIR/send_gate.sh"
check $? "send_gate.sh 존재 + 실행 가능"

grep -q 'execCommand.*insertText\|insertText' "$HOOKS_DIR/send_gate.sh"
check $? "execCommand/insertText 전송 감지 패턴 존재"

echo ""

# === 5. auto_compile.sh (PostToolUse/Write|Edit) ===
echo "--- 5. auto_compile.sh ---"
test -x "$HOOKS_DIR/auto_compile.sh"
check $? "auto_compile.sh 존재 + 실행 가능"

grep -q 'py_compile' "$HOOKS_DIR/auto_compile.sh"
check $? "py_compile 문법 검증 로직 존재"

grep -q 'hook_incident' "$HOOKS_DIR/auto_compile.sh"
check $? "compile_fail → incident_ledger 연동"

echo ""

# === 6. write_marker.sh (PostToolUse/Write|Edit) ===
echo "--- 6. write_marker.sh ---"
test -x "$HOOKS_DIR/write_marker.sh"
check $? "write_marker.sh 존재 + 실행 가능"

grep -q 'write_marker.flag' "$HOOKS_DIR/write_marker.sh"
check $? "write_marker.flag 생성 로직 존재"

echo ""

# === 7. gpt_followup_post.sh (PostToolUse) ===
echo "--- 7. gpt_followup_post.sh ---"
test -x "$HOOKS_DIR/gpt_followup_post.sh"
check $? "gpt_followup_post.sh 존재 + 실행 가능"

echo ""

# === 8. stop_guard.sh (Stop) ===
echo "--- 8. stop_guard.sh ---"
test -x "$HOOKS_DIR/stop_guard.sh"
check $? "stop_guard.sh 존재 + 실행 가능"

grep -q 'FORBIDDEN_PATTERNS\|forbidden' "$HOOKS_DIR/stop_guard.sh"
check $? "금지 문구 패턴 정의됨"

echo ""

# === 9. gpt_followup_stop.sh (Stop) ===
echo "--- 9. gpt_followup_stop.sh ---"
test -x "$HOOKS_DIR/gpt_followup_stop.sh"
check $? "gpt_followup_stop.sh 존재 + 실행 가능"

echo ""

# === 10. completion_gate.sh (Stop) ===
echo "--- 10. completion_gate.sh ---"
test -x "$HOOKS_DIR/completion_gate.sh"
check $? "completion_gate.sh 존재 + 실행 가능"

grep -q 'write_marker.flag' "$HOOKS_DIR/completion_gate.sh"
check $? "write_marker.flag 타임스탬프 비교 로직 존재"

grep -q 'TASKS.md' "$HOOKS_DIR/completion_gate.sh"
check $? "TASKS.md 갱신 검사 로직 존재"

grep -q 'HANDOFF.md' "$HOOKS_DIR/completion_gate.sh"
check $? "HANDOFF.md 갱신 검사 로직 존재"

grep -q 'hook_incident' "$HOOKS_DIR/completion_gate.sh"
check $? "gate_reject → incident_ledger 연동"

echo ""

# === 11. notify_slack.sh (Notification) ===
echo "--- 11. notify_slack.sh ---"
test -x "$HOOKS_DIR/notify_slack.sh"
check $? "notify_slack.sh 존재 + 실행 가능"

echo ""

# === 12. incident_ledger 검증 ===
echo "--- 12. incident_ledger 검증 ---"
LEDGER="$PROJECT_DIR/.claude/incident_ledger.jsonl"
# incident_ledger.jsonl이 존재하거나 생성 가능한지 확인
touch "$LEDGER" 2>/dev/null
test -f "$LEDGER"
check $? "incident_ledger.jsonl 존재/생성 가능"

# hook_incident 함수 동작 테스트
source "$HOOKS_DIR/hook_common.sh" 2>/dev/null
hook_incident "smoke_test" "smoke_test" "" "smoke test 검증" 2>/dev/null
LAST=$(tail -1 "$LEDGER" 2>/dev/null)
echo "$LAST" | grep -q '"type":"smoke_test"'
check $? "hook_incident() 기록 → JSONL 출력 정상"

# 테스트 데이터 정리 (마지막 줄 제거)
sed -i '$ d' "$LEDGER" 2>/dev/null

echo ""

# === 13. 구 훅 부재 확인 (아카이브 완료) ===
echo "--- 13. 구 훅 부재 확인 ---"
! test -f "$HOOKS_DIR/pre_finish_guard.sh"
check $? "pre_finish_guard.sh 미존재 (completion_gate에 흡수됨)"

! test -f "$HOOKS_DIR/gpt_followup_guard.sh"
check $? "gpt_followup_guard.sh 미존재 (post/stop 분리됨)"

! test -f "$HOOKS_DIR/hook_log.txt" || echo "  [INFO] hook_log.txt 아카이브 잔존 (정상 — 새 로그는 .jsonl)"

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
