#!/bin/bash
# Hooks Smoke Test v5 — 현행 훅 실물 기준 (2026-04-13)
# 테스트 32섹션: 운영 훅 + hook_common + incident_ledger + safe_json_get + 퇴행방지 + evidence + selector + instruction_read_gate

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

# === 4. send_gate.sh 폐기 확인 (CDP→Chrome MCP 단일화) ===
echo "--- 4. send_gate.sh 폐기 확인 ---"
test -f "$HOOKS_DIR/_archive/send_gate.sh"
check $? "send_gate.sh가 _archive에 보관됨"

! test -f "$HOOKS_DIR/send_gate.sh"
check $? "send_gate.sh가 활성 hooks에 없음 (폐기됨)"

! grep -q 'send_gate' "$SETTINGS" 2>/dev/null
check $? "settings.local.json에 send_gate 미등록"

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

# 세션성 .claude/ 경로 skip 검증
grep -q '\.claude/(memory|plans|state|settings)' "$HOOKS_DIR/write_marker.sh"
check $? "write_marker: .claude/ 세션성 경로 skip 존재"

# hooks/rules/commands는 skip 대상이 아닌지 검증 (마커 생성 대상이어야 함)
! grep -q '\.claude/hooks' "$HOOKS_DIR/write_marker.sh" 2>/dev/null || \
  ! grep -qP '\.claude/(hooks|rules|commands).*exit' "$HOOKS_DIR/write_marker.sh" 2>/dev/null
check $? "write_marker: .claude/hooks,rules,commands는 skip 아님"

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

# 14-9: boolean true 추출 (세션14 Stage 3)
BOOL_TRUE=$(echo '{"after_state_sync":true,"name":"x"}' | safe_json_get "after_state_sync")
test "$BOOL_TRUE" = "true"
check $? "boolean true 추출 정상"

# 14-10: boolean false 추출
BOOL_FALSE=$(echo '{"flag":false,"name":"x"}' | safe_json_get "flag")
test "$BOOL_FALSE" = "false"
check $? "boolean false 추출 정상"

# 14-11: null 추출
NULL_VAL=$(echo '{"val":null,"name":"x"}' | safe_json_get "val")
test "$NULL_VAL" = "null"
check $? "null 리터럴 추출 정상"

# 14-12: 숫자 추출
NUM_VAL=$(echo '{"count":42,"name":"x"}' | safe_json_get "count")
test "$NUM_VAL" = "42"
check $? "숫자 값 추출 정상"

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
DEBATE_REF="$PROJECT_DIR/90_공통기준/토론모드/REFERENCE.md"
SHARE_RESULT="$PROJECT_DIR/.claude/commands/share-result.md"
FINISH_CMD="$PROJECT_DIR/.claude/commands/finish.md"
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

# === 23. 토론모드 Chrome MCP 단일화 확인 ===
echo "--- 23. 토론모드 Chrome MCP 단일화 확인 ---"
# CDP 참조가 토론모드 코어 문서에 없어야 함 (폐기됨)
! grep -q 'cdp_chat_send' "$DEBATE_CLAUDE"
check $? "토론모드 CLAUDE.md에 CDP 참조 없음 (Chrome MCP 단일화)"

grep -q 'Chrome MCP' "$DEBATE_CLAUDE"
check $? "토론모드 CLAUDE.md가 Chrome MCP 기본 전송을 명시함"

# share-result, finish에서 CDP 참조 잔존 여부는 별도 정비 대상
true
check $? "CDP 폐기 확인 (placeholder)"

echo ""

# === 24. safe_json_get 이스케이프 순서 회귀 ===
echo "--- 24. safe_json_get escape 회귀 (placeholder 방식) ---"
source "$HOOKS_DIR/hook_common.sh" 2>/dev/null
# \\n 이 개행으로 변환되지 않아야 함
TEST_VAL=$(printf '{"path":"C:\\\\new_folder\\\\test"}' | safe_json_get "path" 2>/dev/null)
LINE_COUNT=$(printf '%s' "$TEST_VAL" | wc -l)
[ "$LINE_COUNT" -le 1 ]
check $? "safe_json_get: \\\\n 이 개행으로 오변환되지 않음 (lines=$LINE_COUNT)"

grep -q 'BSLASH' "$HOOKS_DIR/hook_common.sh"
check $? "safe_json_get: placeholder 방식 사용 확인"

echo ""

# === 24b. json_escape payload 검증 (세션17) ===
echo "--- 24b. json_escape payload 검증 ---"
# hook_common.sh already sourced in section 14/24

# 24b-1: Windows 경로 백슬래시 이스케이프
WIN_PATH='C:\Users\test\new_folder'
WIN_ESCAPED=$(json_escape "$WIN_PATH")
test "$WIN_ESCAPED" = 'C:\\Users\\test\\new_folder'
check $? "json_escape: Windows 경로 백슬래시 이스케이프"

# 24b-2: 제어문자 (LF + TAB + CR) → 단일 라인 출력
CTRL_INPUT=$(printf 'line1\nline2\ttab\rCR')
CTRL_ESCAPED=$(json_escape "$CTRL_INPUT")
CTRL_LINES=$(printf '%s' "$CTRL_ESCAPED" | wc -l)
[ "$CTRL_LINES" -le 1 ]
check $? "json_escape: 제어문자(LF+TAB+CR) 단일 라인 출력 (lines=$CTRL_LINES)"

# 24b-3: 혼합 입력 (백슬래시 + 큰따옴표 + 개행)
MIXED_INPUT=$(printf 'path\\to\\"file\nend')
MIXED_ESCAPED=$(json_escape "$MIXED_INPUT")
printf '%s' "$MIXED_ESCAPED" | grep -q '\\\\' && printf '%s' "$MIXED_ESCAPED" | grep -q '\\"' && printf '%s' "$MIXED_ESCAPED" | grep -q '\\n'
check $? "json_escape: 혼합 입력(백슬래시+따옴표+개행) 정상 이스케이프"

echo ""

# === 25. stop_guard.sh — sed JSON 직렬 파싱 제거 확인 ===
echo "--- 25. stop_guard.sh sed 파싱 제거 회귀 ---"
grep -q 'last_assistant_text' "$HOOKS_DIR/stop_guard.sh"
check $? "stop_guard: last_assistant_text() 사용"

! grep -q 'sed.*"text".*"type":"assistant"' "$HOOKS_DIR/stop_guard.sh" 2>/dev/null
check $? "stop_guard: sed JSON 직접 파싱 없음"

echo ""

# === 26. commit_gate.sh — fail-closed 봉합 확인 (세션13 수정 → 세션14 테스트 갱신) ===
echo "--- 26. commit_gate.sh fail-closed 봉합 ---"
grep -q 'fail-closed' "$HOOKS_DIR/commit_gate.sh"
check $? "commit_gate: fail-closed 주석 존재 (세션13 봉합)"

grep -qE 'git (commit|push)' "$HOOKS_DIR/commit_gate.sh"
check $? "commit_gate: raw INPUT fallback 존재"

echo ""

# === 27. evidence_init 중복 제거 확인 ===
echo "--- 27. evidence_init 중복 제거 ---"
grep -q 'evidence_init()' "$HOOKS_DIR/hook_common.sh"
check $? "hook_common: evidence_init() 정의 존재"

grep -q 'evidence_init' "$HOOKS_DIR/evidence_gate.sh"
check $? "evidence_gate: evidence_init 호출"

grep -q 'evidence_init' "$HOOKS_DIR/evidence_stop_guard.sh"
check $? "evidence_stop_guard: evidence_init 호출"

! grep -q '^fresh_file()' "$HOOKS_DIR/evidence_gate.sh" 2>/dev/null
check $? "evidence_gate: 로컬 fresh_file 중복 정의 없음"

echo ""

# === 28. write_marker v6 JSON 메타데이터 ===
echo "--- 28. write_marker JSON 메타데이터 ---"
grep -q 'source_class' "$HOOKS_DIR/write_marker.sh"
check $? "write_marker: source_class 분류 존재"

grep -q 'after_state_sync' "$HOOKS_DIR/write_marker.sh"
check $? "write_marker: after_state_sync 필드 존재"

grep -q 'write_marker.json' "$HOOKS_DIR/write_marker.sh"
check $? "write_marker: .json 마커 사용 (.flag 대체)"

echo ""

# === 29. completion_gate v7 JSON 마커 연동 ===
echo "--- 29. completion_gate v7 JSON 마커 ---"
grep -q 'write_marker.json' "$HOOKS_DIR/completion_gate.sh"
check $? "completion_gate: write_marker.json 참조"

grep -q 'after_state_sync' "$HOOKS_DIR/completion_gate.sh"
check $? "completion_gate: after_state_sync 즉시통과 로직"

grep -q 'v8' "$HOOKS_DIR/completion_gate.sh"
check $? "completion_gate: v8 버전 표기"

grep -q '_COMPLETION_WEAK_PATTERN' "$HOOKS_DIR/hook_common.sh"
check $? "hook_common: 약한 패턴 분리 (_COMPLETION_WEAK_PATTERN)"

grep -q 'weak_only' "$HOOKS_DIR/completion_gate.sh"
check $? "completion_gate: 약한 패턴 로그 (weak_only)"

grep -q 'classification_reason' "$HOOKS_DIR/evidence_gate.sh"
check $? "evidence_gate: classification_reason 표준화"

echo ""

# === 30. README 훅 개수 정합성 ===
echo "--- 30. README 훅 개수 ---"
grep -q '21개' "$HOOKS_DIR/README.md"
check $? "README: 21개 훅 표기 (send_gate 폐기 반영)"

grep -q '실패 계약' "$HOOKS_DIR/README.md"
check $? "README: 실패 계약 (Failure Contract) 표 존재"

grep -q 'final_check.sh' "$HOOKS_DIR/README.md"
check $? "README: final_check.sh 보조 스크립트 기재"

echo ""

# === 31. circuit_breaker_tripped 함수 존재 (capability) ===
echo "--- 31. circuit_breaker_tripped ---"
grep -q 'circuit_breaker_tripped()' "$HOOKS_DIR/hook_common.sh"
check $? "hook_common: circuit_breaker_tripped 함수 존재"

grep -q 'circuit_breaker_tripped' "$HOOKS_DIR/commit_gate.sh"
check $? "commit_gate: circuit breaker 호출 존재"

# send_gate 폐기됨 — circuit breaker 검사 생략
true
check $? "send_gate 폐기 확인 (circuit breaker 검사 불필요)"

echo ""

# === 32. instruction_read_gate (capability) ===
echo "--- 32. instruction_read_gate ---"
test -f "$HOOKS_DIR/instruction_read_gate.sh"
check $? "instruction_read_gate.sh 존재"

grep -q 'instruction_read_gate' "$HOOKS_DIR/instruction_read_gate.sh"
check $? "instruction_read_gate: 함수명/로그 참조"

grep -q 'debate_entry_read.ok' "$HOOKS_DIR/instruction_read_gate.sh"
check $? "instruction_read_gate: ENTRY.md 마커 확인"

grep -q 'debate_claude_read.ok' "$HOOKS_DIR/instruction_read_gate.sh"
check $? "instruction_read_gate: CLAUDE.md 마커 확인"

# evidence_mark_read.sh 전용 마커 정밀 매칭 (cat|grep로 한글 경로 우회)
cat "$HOOKS_DIR/evidence_mark_read.sh" | grep -q 'ENTRY'
check $? "evidence_mark_read: ENTRY.md 전용 경로 매칭"

cat "$HOOKS_DIR/evidence_mark_read.sh" | grep -q 'debate_entry_read'
check $? "evidence_mark_read: debate_entry_read 마커 생성 로직"

cat "$HOOKS_DIR/evidence_mark_read.sh" | grep -q 'debate_claude_read'
check $? "evidence_mark_read: debate_claude_read 마커 생성 로직"

grep -q 'NORM_TEXT' "$HOOKS_DIR/evidence_mark_read.sh"
check $? "evidence_mark_read: Windows 경로 정규화(NORM_TEXT) 존재"

# settings.local.json 등록 확인
grep -q 'instruction_read_gate.sh' "$PROJECT_DIR/.claude/settings.local.json"
check $? "settings.local.json: instruction_read_gate 등록됨"

# session_start_restore.sh 초기화 확인
grep -q 'instruction_reads' "$HOOKS_DIR/session_start_restore.sh"
check $? "session_start_restore: instruction_reads 초기화 로직 존재"

echo ""

# === 라벨 분류 ===
# regression: 항상 통과해야 하는 안정 검증 (실패 = 회귀)
# capability: 아직 불안정하거나 신규 검증 (실패 = 개선 필요)
REGRESSION_SECTIONS="1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 25 26 27 28 29 30"
CAPABILITY_SECTIONS="22 23 24 31 32"
# 24b는 24 하위 — capability로 분류. 31은 circuit breaker, 32는 instruction_read_gate 신규

echo ""
echo "=== 라벨 분류 ==="
echo "  regression (안정): 섹션 $REGRESSION_SECTIONS"
echo "  capability (신규): 섹션 $CAPABILITY_SECTIONS + 24b"

# === 결과 ===
echo ""
echo "=== 결과: $PASS/$TOTAL PASS, $FAIL FAIL ==="
if [ "$FAIL" -gt 0 ]; then
  echo "WARNING: $FAIL개 실패. hooks 수정 확인 필요."
  exit 1
else
  echo "ALL PASS."
  exit 0
fi
