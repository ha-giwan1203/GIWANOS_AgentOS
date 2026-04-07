#!/bin/bash
# Hooks Smoke Test v4 — 현행 훅 실물 기준 (2026-04-08)
# 운영 훅 22개 + hook_common + incident_ledger 검증 (evidence 5종 + selector 추가)

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

echo "=== Hooks Smoke Test v4 ==="
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

# === 11. commit_gate.sh (PreToolUse/Bash) ===
echo "--- 11. commit_gate.sh ---"
test -x "$HOOKS_DIR/commit_gate.sh"
check $? "commit_gate.sh 존재 + 실행 가능"

grep -q 'final_check' "$HOOKS_DIR/commit_gate.sh"
check $? "final_check 호출 로직 존재"

grep -q 'git.*commit\|git.*push' "$HOOKS_DIR/commit_gate.sh"
check $? "git commit/push 감지 패턴 존재"

echo ""

# === 12. notify_slack.sh (Notification) ===
echo "--- 12. notify_slack.sh ---"
test -x "$HOOKS_DIR/notify_slack.sh"
check $? "notify_slack.sh 존재 + 실행 가능"

echo ""

# === 13. incident_ledger 검증 ===
echo "--- 13. incident_ledger 검증 ---"
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

# === 14. safe_json_get 엣지케이스 검증 (GPT+Claude 합의 P2) ===
echo "--- 14. safe_json_get 엣지케이스 ---"
source "$HOOKS_DIR/hook_common.sh" 2>/dev/null

# 14-1: 이스케이프된 따옴표 포함 값
ESCAPED_RESULT=$(echo '{"command":"echo \"hello world\""}' | safe_json_get "command")
echo "$ESCAPED_RESULT" | grep -q 'echo "hello world"'
check $? "escaped quotes 처리 정상"

# 14-2: 멀티라인 입력 (줄바꿈 포함 JSON)
MULTILINE_RESULT=$(printf '{\n  "command": "ls -la"\n}' | safe_json_get "command")
test "$MULTILINE_RESULT" = "ls -la"
check $? "multiline JSON 입력 처리 정상"

# 14-3: 중첩 JSON 값 (객체 값 추출)
NESTED_RESULT=$(echo '{"tool_name":"Bash","tool_input":{"cmd":"test"}}' | safe_json_get "tool_name")
test "$NESTED_RESULT" = "Bash"
check $? "중첩 JSON에서 문자열 키 추출 정상"

# 14-4: 빈 값 / 키 없음
EMPTY_RESULT=$(echo '{"other":"val"}' | safe_json_get "command")
test -z "$EMPTY_RESULT"
check $? "존재하지 않는 키 → 빈 결과"

# 14-5: Python 파일조작 차단 패턴 존재 확인
grep -qE 'os\.remove|shutil' "$HOOKS_DIR/block_dangerous.sh"
check $? "block_dangerous.sh에 Python 파일조작 탐지 패턴 존재"

# 14-6: tool_input 중첩 객체 추출 (GPT 3차 피드백)
NESTED_OBJ=$(echo '{"tool_name":"Bash","tool_input":{"cmd":"ls"}}' | safe_json_get "tool_input")
echo "$NESTED_OBJ" | grep -q 'cmd'
check $? "tool_input 중첩 객체 추출 정상"

# 14-7: 문자열 안 } 포함 케이스
BRACE_RESULT=$(echo '{"command":"echo }done"}' | safe_json_get "command")
echo "$BRACE_RESULT" | grep -q '}done'
check $? "문자열 값 내 } 포함 시 정상 추출"

# 14-8: \\n 이스케이프 복원
NEWLINE_RESULT=$(echo '{"msg":"line1\\nline2"}' | safe_json_get "msg")
echo "$NEWLINE_RESULT" | grep -q 'line2'
check $? "\\n 이스케이프 → 개행 복원 정상"

echo ""

# === 15. 퇴행 방지: 구 로그 직접 참조 0건 ===
echo "--- 15. 퇴행 방지 (hook_log.txt 직접 참조) ---"
# smoke_test.sh 자신(INFO 표시용)은 제외
STALE_REFS=$(grep -l 'hook_log\.txt' "$HOOKS_DIR"/*.sh 2>/dev/null | grep -v smoke_test.sh | grep -v final_check.sh | wc -l)
test "$STALE_REFS" -eq 0
check $? "운영 훅에서 hook_log.txt 직접 참조 0건 (JSONL 통일)"

echo ""

# === 16. 구 훅 부재 확인 (아카이브 완료) ===
echo "--- 16. 구 훅 부재 확인 ---"
! test -f "$HOOKS_DIR/pre_finish_guard.sh"
check $? "pre_finish_guard.sh 미존재 (completion_gate에 흡수됨)"

! test -f "$HOOKS_DIR/gpt_followup_guard.sh"
check $? "gpt_followup_guard.sh 미존재 (post/stop 분리됨)"

! test -f "$HOOKS_DIR/hook_log.txt" || echo "  [INFO] hook_log.txt 아카이브 잔존 (정상 — 새 로그는 .jsonl)"

echo ""

# === 17. evidence_gate.sh (PreToolUse/Bash|Write|Edit) ===
echo "--- 17. evidence_gate.sh (증거 없는 위험실행 차단) ---"
test -x "$HOOKS_DIR/evidence_gate.sh"
check $? "evidence_gate.sh 존재 + 실행 가능"

bash -n "$HOOKS_DIR/evidence_gate.sh" 2>/dev/null
check $? "evidence_gate.sh 구문 검증 (bash -n)"

grep -q 'fresh_req\|fresh_ok' "$HOOKS_DIR/evidence_gate.sh"
check $? "req/ok 판정 로직 존재"

grep -q 'deny.*date_check' "$HOOKS_DIR/evidence_gate.sh"
check $? "date_check req→deny 분기 존재"

echo ""

# === 18. evidence_stop_guard.sh (Stop) ===
echo "--- 18. evidence_stop_guard.sh (근거 없는 결론 차단) ---"
test -x "$HOOKS_DIR/evidence_stop_guard.sh"
check $? "evidence_stop_guard.sh 존재 + 실행 가능"

bash -n "$HOOKS_DIR/evidence_stop_guard.sh" 2>/dev/null
check $? "evidence_stop_guard.sh 구문 검증 (bash -n)"

grep -qE '로그인 실패|수동 로그인' "$HOOKS_DIR/evidence_stop_guard.sh"
check $? "금지 결론 패턴 (로그인 실패/수동 로그인) 존재"

grep -qE '완료|PASS' "$HOOKS_DIR/evidence_stop_guard.sh"
check $? "금지 결론 패턴 (완료/PASS) 존재"

echo ""

# === 19. evidence_mark_read.sh (PostToolUse) ===
echo "--- 19. evidence_mark_read.sh (증거 마커 적립) ---"
test -x "$HOOKS_DIR/evidence_mark_read.sh"
check $? "evidence_mark_read.sh 존재 + 실행 가능"

bash -n "$HOOKS_DIR/evidence_mark_read.sh" 2>/dev/null
check $? "evidence_mark_read.sh 구문 검증 (bash -n)"

grep -q 'mark.*skill_read' "$HOOKS_DIR/evidence_mark_read.sh"
check $? "skill_read 마커 적립 로직 존재"

grep -q 'mark.*tasks_updated' "$HOOKS_DIR/evidence_mark_read.sh"
check $? "tasks_updated 마커 적립 로직 존재"

echo ""

# === 20. risk_profile_prompt.sh (UserPromptSubmit) ===
echo "--- 20. risk_profile_prompt.sh (위험 프롬프트 req 생성) ---"
test -x "$HOOKS_DIR/risk_profile_prompt.sh"
check $? "risk_profile_prompt.sh 존재 + 실행 가능"

bash -n "$HOOKS_DIR/risk_profile_prompt.sh" 2>/dev/null
check $? "risk_profile_prompt.sh 구문 검증 (bash -n)"

grep -q 'touch_req.*date_check' "$HOOKS_DIR/risk_profile_prompt.sh"
check $? "date_check req 생성 로직 존재"

grep -q 'touch_req.*auth_diag' "$HOOKS_DIR/risk_profile_prompt.sh"
check $? "auth_diag req 생성 로직 존재"

echo ""

# === 21. date_scope_guard.sh (PreToolUse/Bash) ===
echo "--- 21. date_scope_guard.sh (위험 날짜 차단) ---"
test -x "$HOOKS_DIR/date_scope_guard.sh"
check $? "date_scope_guard.sh 존재 + 실행 가능"

bash -n "$HOOKS_DIR/date_scope_guard.sh" 2>/dev/null
check $? "date_scope_guard.sh 구문 검증 (bash -n)"

grep -qE '일요일|%u.*7' "$HOOKS_DIR/date_scope_guard.sh"
check $? "일요일(요일 7) 차단 로직 존재"

grep -q 'MM/DD' "$HOOKS_DIR/date_scope_guard.sh"
check $? "MM/DD 형식 차단 패턴 존재"

echo ""

# === 22. 토론모드 selector 문서 정합성 ===
echo "--- 22. 토론모드 selector 문서 정합성 ---"
DEBATE_CLAUDE="$PROJECT_DIR/90_공통기준/토론모드/CLAUDE.md"
test -f "$DEBATE_CLAUDE"
check $? "토론모드 CLAUDE.md 존재"

grep -q '#prompt-textarea' "$DEBATE_CLAUDE"
check $? "입력창 selector (#prompt-textarea) 문서화됨"

grep -q 'data-testid="send-button"' "$DEBATE_CLAUDE"
check $? "전송버튼 selector (send-button) 문서화됨"

grep -q 'data-testid="stop-button"' "$DEBATE_CLAUDE"
check $? "중지버튼 selector (stop-button) 문서화됨"

grep -q 'data-message-author-role="assistant"' "$DEBATE_CLAUDE"
check $? "응답노드 selector (assistant role) 문서화됨"

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
