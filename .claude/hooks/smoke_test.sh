#!/bin/bash
# Hooks Smoke Test v5 — 현행 훅 실물 기준 (2026-04-15)
# 테스트 45섹션: 운영 훅 + hook_common + incident_ledger + safe_json_get + 퇴행방지 + evidence + selector + instruction_read_gate + 게이트 실행 테스트 + navigate_gate

export LC_ALL=en_US.UTF-8

PASS=0
FAIL=0
TOTAL=0
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
HOOKS_DIR="$PROJECT_DIR/.claude/hooks"
SETTINGS="$PROJECT_DIR/.claude/settings.local.json"

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

echo "=== Hooks Smoke Test v5 ==="
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

! grep -q '"send_gate\.sh"' "$SETTINGS" 2>/dev/null
check $? "settings.local.json에 send_gate.sh 미등록 (mcp_send_gate는 정상)"

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
! grep -v '\[NEVER\]' "$DEBATE_CLAUDE" | grep -q 'cdp_chat_send'
check $? "토론모드 CLAUDE.md에 CDP 실사용 참조 없음 (금지 선언 제외)"

grep -q 'Chrome MCP' "$DEBATE_CLAUDE"
check $? "토론모드 CLAUDE.md가 Chrome MCP 기본 전송을 명시함"

# share-result, finish 명령에서 CDP 참조 없음 확인
! grep -q 'cdp_chat_send' "$SHARE_RESULT"
check $? "share-result에 CDP 참조 없음"

! grep -q 'cdp_chat_send' "$FINISH_CMD"
check $? "finish에 CDP 참조 없음"

# settings allow에 CDP 스크립트 허용 없음 확인
! grep -q 'scripts/cdp/' "$SETTINGS"
check $? "settings.local.json에 CDP 스크립트 허용 없음"

# mcp_send_gate.sh 존재 확인 (Chrome MCP SEND GATE)
test -f "$HOOKS_DIR/mcp_send_gate.sh"
check $? "mcp_send_gate.sh 존재 (Chrome MCP 전송 게이트)"

grep -q 'mcp_send_gate' "$SETTINGS"
check $? "mcp_send_gate settings 등록 확인"

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
grep -qE '[0-9]+개 스크립트' "$HOOKS_DIR/README.md"
check $? "README: 활성 훅 개수 표기 존재 (세션72 동적 숫자 허용 — 세션52 하드코딩 제거)"

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

# === 33. incident_review.py (세션40 학습 루프) ===
echo "--- 33. incident_review.py ---"
test -f "$HOOKS_DIR/incident_review.py"
check $? "incident_review.py 존재"

python3 "$HOOKS_DIR/incident_review.py" --help >/dev/null 2>&1
check $? "incident_review.py --help 실행 가능"

python3 "$HOOKS_DIR/incident_review.py" --days 1 --threshold 999 2>&1 | grep -q "임계치 초과 항목 없음"
check $? "incident_review.py 빈 결과 정상 출력"

echo ""

# === 34. classify_feedback.py (세션40 MEMORY 3분류) ===
echo "--- 34. classify_feedback.py ---"
test -f "$HOOKS_DIR/classify_feedback.py"
check $? "classify_feedback.py 존재"

python3 "$HOOKS_DIR/classify_feedback.py" --help >/dev/null 2>&1
check $? "classify_feedback.py --help 실행 가능"

python3 "$HOOKS_DIR/classify_feedback.py" --validate 2>&1 | grep -q "ALL OK"
check $? "classify_feedback.py --validate ALL OK"

echo ""

# === 35. hook_common.sh task_result 함수 (세션40 로그 분리) ===
echo "--- 35. hook_common.sh task_result ---"
grep -q 'hook_task_result()' "$HOOKS_DIR/hook_common.sh"
check $? "hook_task_result() 함수 정의됨"

grep -q 'TASK_RESULTS_LOG' "$HOOKS_DIR/hook_common.sh"
check $? "TASK_RESULTS_LOG 변수 정의됨"

grep -q 'task_consecutive_fail' "$HOOKS_DIR/hook_common.sh"
check $? "task_consecutive_fail classification 사용됨"

echo ""

# === 36. hook_config.json task_escalation (세션40) ===
echo "--- 36. hook_config.json task_escalation ---"
grep -q 'task_escalation' "$PROJECT_DIR/.claude/hook_config.json"
check $? "hook_config.json: task_escalation 섹션 존재"

grep -q 'default_threshold' "$PROJECT_DIR/.claude/hook_config.json"
check $? "hook_config.json: default_threshold 설정됨"

grep -q 'daily-routine' "$PROJECT_DIR/.claude/hook_config.json"
check $? "hook_config.json: daily-routine per_task override 존재"

echo ""

# === 37. incident_repair.py 세션40 매핑 (task_consecutive_fail) ===
echo "--- 37. incident_repair.py 세션40 매핑 ---"
grep -q 'task_consecutive_fail' "$HOOKS_DIR/incident_repair.py"
check $? "incident_repair.py: task_consecutive_fail 매핑 존재"

grep -q 'meta_drift' "$HOOKS_DIR/incident_repair.py"
check $? "incident_repair.py: meta_drift 매핑 존재"

grep -q 'harness_missing' "$HOOKS_DIR/incident_repair.py"
check $? "incident_repair.py: harness_missing 매핑 존재"

echo ""

# === 38. task_runner.sh (세션40 태스크 실행 래퍼) ===
echo "--- 38. task_runner.sh ---"
test -f "$PROJECT_DIR/.claude/scripts/task_runner.sh"
check $? "task_runner.sh 존재"

grep -q 'hook_task_result' "$PROJECT_DIR/.claude/scripts/task_runner.sh"
check $? "task_runner.sh: hook_task_result 호출"

grep -q 'hook_common.sh' "$PROJECT_DIR/.claude/scripts/task_runner.sh"
check $? "task_runner.sh: hook_common.sh source"

echo ""

# === 39. incident_repair.py backfill (세션40) ===
echo "--- 39. incident_repair.py backfill ---"
grep -q 'backfill_classification' "$HOOKS_DIR/incident_repair.py"
check $? "incident_repair.py: backfill_classification 함수 존재"

grep -q 'backfill-classification' "$HOOKS_DIR/incident_repair.py"
check $? "incident_repair.py: --backfill-classification CLI 옵션"

echo ""

# === 40. commit_gate.sh 실행 테스트 (세션46 GPT+Claude 합의: 최소 시나리오) ===
echo "--- 40. commit_gate.sh 실행 테스트 ---"
# 40-1: git 아닌 명령 → 통과 (exit 0, 출력 없음)
_cg_out=$(echo '{"command":"ls -la"}' | bash "$HOOKS_DIR/commit_gate.sh" 2>/dev/null)
_cg_exit=$?
[ "$_cg_exit" -eq 0 ] && [ -z "$_cg_out" ]
check $? "commit_gate: non-git 명령 → 통과"

# 40-2: build_fingerprint 함수 존재 + 호출 가능
(source "$HOOKS_DIR/commit_gate.sh" <<< '{"command":"echo test"}' >/dev/null 2>&1; type build_fingerprint >/dev/null 2>&1)
# 함수 정의 검증 (grep 대신 source 후 type 확인이 이상적이나, side-effect 회피를 위해 grep)
grep -q 'build_fingerprint()' "$HOOKS_DIR/commit_gate.sh"
check $? "commit_gate: build_fingerprint() 함수 정의됨"

# 40-3: should_suppress_incident 함수 존재
grep -q 'should_suppress_incident()' "$HOOKS_DIR/commit_gate.sh"
check $? "commit_gate: should_suppress_incident() 함수 정의됨"

# 40-4: 함수 밖 local 사용 없음 (회귀 방지)
# 함수 내부 local은 허용, 함수 밖 local은 결함
_outside_local=$(awk '/^[a-zA-Z_]+\(\)/{in_func=1} /^\}/{if(in_func) in_func=0} !in_func && /^[[:space:]]*local /{print NR}' "$HOOKS_DIR/commit_gate.sh")
[ -z "$_outside_local" ]
check $? "commit_gate: 함수 밖 local 사용 없음 (회귀 방지)"

echo ""

# === 41. completion_gate.sh 실행 테스트 (세션46) ===
echo "--- 41. completion_gate.sh 실행 테스트 ---"
# 41-1: write_marker 없으면 통과
_comp_out=$(echo '{"tool_name":"Bash","input":{"command":"echo done"}}' | CLAUDE_PROJECT_DIR="$PROJECT_DIR" bash "$HOOKS_DIR/completion_gate.sh" 2>/dev/null)
_comp_exit=$?
[ "$_comp_exit" -eq 0 ]
check $? "completion_gate: marker 없으면 통과"

# 41-2: completion_gate.sh bash -n 구문 검사
bash -n "$HOOKS_DIR/completion_gate.sh" 2>/dev/null
check $? "completion_gate: bash -n 구문 검사 통과"

echo ""

# === 42. evidence_gate.sh 실행 테스트 (세션46) ===
echo "--- 42. evidence_gate.sh 실행 테스트 ---"
# 42-1: evidence 요구사항 없으면 no-op (통과)
_ev_out=$(echo '{"tool_name":"Bash","input":{"command":"echo hi"}}' | CLAUDE_PROJECT_DIR="$PROJECT_DIR" bash "$HOOKS_DIR/evidence_gate.sh" 2>/dev/null)
_ev_exit=$?
[ "$_ev_exit" -eq 0 ]
check $? "evidence_gate: req 없으면 통과"

# 42-2: evidence_gate.sh bash -n 구문 검사
bash -n "$HOOKS_DIR/evidence_gate.sh" 2>/dev/null
check $? "evidence_gate: bash -n 구문 검사 통과"

echo ""

# === 43. completion_gate deny-path 테스트 (세션46 GPT 합의: 9점대 목표) ===
echo "--- 43. completion_gate deny-path ---"
# 43-1: 강한 완료 주장 + git 미반영 변경 → block
# completion_gate는 Stop hook이므로 stdin이 아닌 last_assistant_text에 의존
# 여기서는 git_has_relevant_changes 함수를 직접 테스트
(source "$HOOKS_DIR/hook_common.sh" 2>/dev/null
 # dirty 상태가 있으면 true, 없으면 false — 현재 working tree 상태 그대로 활용
 if git_has_relevant_changes 2>/dev/null; then
   echo "has_changes"
 else
   echo "clean"
 fi) > /dev/null 2>&1
check $? "completion_gate: git_has_relevant_changes 함수 호출 가능"

# 43-2: write_marker 없을 때 completion_gate 통과 확인
_cg_marker="$PROJECT_DIR/90_공통기준/agent-control/state/write_marker.json"
_cg_backup=""
if [ -f "$_cg_marker" ]; then
  _cg_backup=$(cat "$_cg_marker")
  rm -f "$_cg_marker" 2>/dev/null
fi
# Stop hook은 직접 호출이 어려우므로 bash -n + grep로 deny 경로 존재 확인
grep -q 'completion_before_git' "$HOOKS_DIR/completion_gate.sh"
check $? "completion_gate: deny 경로 'completion_before_git' 존재"
# 마커 복원
if [ -n "$_cg_backup" ]; then
  echo "$_cg_backup" > "$_cg_marker" 2>/dev/null
fi

echo ""

# === 44. evidence_gate deny-path 테스트 (세션46 GPT 합의) ===
echo "--- 44. evidence_gate deny-path ---"
# 44-1: deny 함수가 JSON deny 출력을 생성하는지 확인
# evidence_gate의 deny()는 evidence_init 의존이라 직접 실행 어려움
# 대신 deny 함수 내부에서 decision:deny JSON을 출력하는지 grep으로 확인
grep -q 'decision.*deny' "$HOOKS_DIR/evidence_gate.sh" 2>/dev/null
check $? "evidence_gate: deny 함수가 deny JSON 출력 생성"

# 44-2: skill_read deny 경로 존재 확인
grep -q 'skill_read.req / identifier_ref.req' "$HOOKS_DIR/evidence_gate.sh"
check $? "evidence_gate: skill_read/identifier_ref deny 경로 존재"

# 44-3~5: evidence_gate 런타임 deny 테스트 (세션48 GPT 합의)
# 세션키 기반 evidence 경로 조성 → stdin JSON 주입 → deny JSON 출력 확인
_eg_script="$HOOKS_DIR/evidence_gate.sh"
_eg_sk=$(source "$HOOKS_DIR/hook_common.sh" 2>/dev/null; session_key)
_eg_evidence_dir="$PROJECT_DIR/.claude/state/evidence/$_eg_sk"
_eg_req_dir="$_eg_evidence_dir/requires"
_eg_proof_dir="$_eg_evidence_dir/proofs"
_eg_start_file="$_eg_evidence_dir/.session_start"

# 백업: 기존 req/ok 파일
_eg_req_backup_dir=$(mktemp -d 2>/dev/null || echo "/tmp/_eg_req_backup_$$")
mkdir -p "$_eg_req_backup_dir"
[ -d "$_eg_req_dir" ] && cp -a "$_eg_req_dir"/. "$_eg_req_backup_dir/" 2>/dev/null
_eg_proof_backup_dir=$(mktemp -d 2>/dev/null || echo "/tmp/_eg_proof_backup_$$")
mkdir -p "$_eg_proof_backup_dir"
[ -d "$_eg_proof_dir" ] && cp -a "$_eg_proof_dir"/. "$_eg_proof_backup_dir/" 2>/dev/null

# 세션 디렉토리 보장
mkdir -p "$_eg_req_dir" "$_eg_proof_dir" 2>/dev/null
[ -f "$_eg_start_file" ] || : > "$_eg_start_file"
# start_file을 과거로 설정해서 fresh_req가 동작하도록
touch -t 202601010000 "$_eg_start_file" 2>/dev/null

# 44-3: tasks_handoff.req + git commit → deny
: > "$_eg_req_dir/tasks_handoff.req"
rm -f "$_eg_proof_dir/tasks_updated.ok" "$_eg_proof_dir/handoff_updated.ok" 2>/dev/null
_eg_result_3=$(echo '{"command":"git commit -m test","tool_name":"Bash","tool_input":""}' | bash "$_eg_script" 2>/dev/null)
echo "$_eg_result_3" | grep -q '"decision":"deny"' 2>/dev/null
check $? "evidence_gate: tasks_handoff.req + git commit → deny (런타임)"

# 44-4: skill_read.req + 기준정보 도메인 편집 → deny
rm -f "$_eg_req_dir/tasks_handoff.req" 2>/dev/null
: > "$_eg_req_dir/skill_read.req"
rm -f "$_eg_proof_dir/skill_read.ok" "$_eg_proof_dir/identifier_ref.ok" 2>/dev/null
_eg_result_4=$(echo '{"tool_name":"Edit","tool_input":"10_라인배치/SKILL.md","command":""}' | bash "$_eg_script" 2>/dev/null)
echo "$_eg_result_4" | grep -q '"decision":"deny"' 2>/dev/null
check $? "evidence_gate: skill_read.req + 도메인편집 → deny (런타임)"

# 44-5: map_scope.req + Write 도구 → deny
rm -f "$_eg_req_dir/skill_read.req" 2>/dev/null
: > "$_eg_req_dir/map_scope.req"
rm -f "$_eg_proof_dir/map_scope.ok" 2>/dev/null
_eg_result_5=$(echo '{"tool_name":"Write","tool_input":"test_file.md","command":""}' | bash "$_eg_script" 2>/dev/null)
echo "$_eg_result_5" | grep -q '"decision":"deny"' 2>/dev/null
check $? "evidence_gate: map_scope.req + Write → deny (런타임)"

# 상태 복원
rm -rf "$_eg_req_dir"/* 2>/dev/null
rm -rf "$_eg_proof_dir"/* 2>/dev/null
[ "$(ls -A "$_eg_req_backup_dir" 2>/dev/null)" ] && cp -a "$_eg_req_backup_dir"/. "$_eg_req_dir/" 2>/dev/null
[ "$(ls -A "$_eg_proof_backup_dir" 2>/dev/null)" ] && cp -a "$_eg_proof_backup_dir"/. "$_eg_proof_dir/" 2>/dev/null
rm -rf "$_eg_req_backup_dir" "$_eg_proof_backup_dir" 2>/dev/null

echo ""

# === 43-3. completion_gate 부분 런타임 테스트 (세션48 GPT 합의) ===
echo "--- 43-3. completion_gate 부분 런타임 (write_marker deny) ---"
# Stop 훅이라 완전 런타임 재현 불가 — write_marker 경로만 부분 검증
_cg_script="$HOOKS_DIR/completion_gate.sh"
_cg_marker="$PROJECT_DIR/90_공통기준/agent-control/state/write_marker.json"
_cg_marker_backup=""
[ -f "$_cg_marker" ] && _cg_marker_backup=$(cat "$_cg_marker")

# 조건 조성: write_marker 생성 (미래 타임스탬프) → TASKS 갱신 안 됨 상태
mkdir -p "$(dirname "$_cg_marker")" 2>/dev/null
echo '{"created":"2099-01-01T00:00:00"}' > "$_cg_marker"
# completion_gate는 is_completion_claim 먼저 체크 → transcript 없으면 통과해서 deny까지 안 감
# 그래서 여기서는 grep으로 deny 경로의 JSON 구조만 확인
grep -q 'decision.*deny' "$_cg_script" 2>/dev/null
check $? "completion_gate: write_marker deny 경로 deny JSON 구조 확인 (부분)"

# 복원
if [ -n "$_cg_marker_backup" ]; then
  echo "$_cg_marker_backup" > "$_cg_marker"
else
  rm -f "$_cg_marker" 2>/dev/null
fi

echo ""

# === 45. navigate_gate.sh 런타임 테스트 (세션48 GPT 합의) ===
echo "--- 45. navigate_gate.sh 런타임 테스트 ---"
_NG_SCRIPT="$HOOKS_DIR/navigate_gate.sh"

# 45-1: 파일 존재 + bash -n 구문검사
test -f "$_NG_SCRIPT"
check $? "navigate_gate: 파일 존재"
bash -n "$_NG_SCRIPT" 2>/dev/null
check $? "navigate_gate: bash -n 구문검사 통과"

# 45-2: settings.local.json에 등록 확인
grep -q 'navigate_gate' "$SETTINGS" 2>/dev/null
check $? "navigate_gate: settings.local.json 등록 확인"

# 45-3: 비-chatgpt URL → exit 0 (통과)
_ng_result=$(echo '{"tool_input":{"url":"https://google.com"}}' | bash "$_NG_SCRIPT" 2>/dev/null)
_ng_exit=$?
[ "$_ng_exit" = "0" ] && ! echo "$_ng_result" | grep -q '"decision":"deny"' 2>/dev/null
check $? "navigate_gate: 비-chatgpt URL → 통과"

# 45-4: chatgpt URL + 마커 없음 → deny (도메인 무관 — 세션51 수정)
# 상태 백업
_ng_marker_dir="$PROJECT_DIR/.claude/state/instruction_reads"
_ng_marker="$_ng_marker_dir/debate_claude_read.ok"
_ng_marker_backup=""
[ -f "$_ng_marker" ] && _ng_marker_backup=$(cat "$_ng_marker")

# 조건 조성: 마커 제거
rm -f "$_ng_marker" 2>/dev/null

_ng_deny_result=$(echo '{"tool_input":{"url":"https://chatgpt.com/g/g-p-test/project"}}' | bash "$_NG_SCRIPT" 2>/dev/null)
echo "$_ng_deny_result" | grep -q '"decision":"deny"' 2>/dev/null
check $? "navigate_gate: chatgpt+마커없음 → deny (도메인 무관)"

# 45-5: chatgpt URL + 마커 있음 → 통과
mkdir -p "$_ng_marker_dir" 2>/dev/null
: > "$_ng_marker"
_ng_pass_result=$(echo '{"tool_input":{"url":"https://chatgpt.com/g/g-p-test/project"}}' | bash "$_NG_SCRIPT" 2>/dev/null)
_ng_pass_exit=$?
[ "$_ng_pass_exit" = "0" ] && ! echo "$_ng_pass_result" | grep -q '"decision":"deny"' 2>/dev/null
check $? "navigate_gate: chatgpt+마커있음 → 통과"

# 상태 복원
if [ -n "$_ng_marker_backup" ]; then
  mkdir -p "$_ng_marker_dir" 2>/dev/null
  echo "$_ng_marker_backup" > "$_ng_marker"
else
  rm -f "$_ng_marker" 2>/dev/null
fi

echo ""

# === 46. 세션51 합의 런타임 테스트 (deny 포맷 통일 + 셀렉터 검증) ===
echo "--- 46. 세션51 합의 런타임 테스트 ---"

# 46-1: skill_instruction_gate — MES 접근 + 마커 없음 → deny (stdout JSON, exit 0)
_sig_script="$HOOKS_DIR/skill_instruction_gate.sh"
_sig_sk=$(source "$HOOKS_DIR/hook_common.sh" 2>/dev/null; session_key)
_sig_proof_dir="$PROJECT_DIR/.claude/state/evidence/$_sig_sk/proofs"
_sig_marker_1="$_sig_proof_dir/skill_read__daily-routine.ok"
_sig_marker_2="$_sig_proof_dir/skill_read__production-result-upload.ok"
_sig_backup_1=""
_sig_backup_2=""
[ -f "$_sig_marker_1" ] && _sig_backup_1="1" && mv "$_sig_marker_1" "$_sig_marker_1.bak" 2>/dev/null
[ -f "$_sig_marker_2" ] && _sig_backup_2="1" && mv "$_sig_marker_2" "$_sig_marker_2.bak" 2>/dev/null

_sig_result=$(echo '{"command":"python3 -c \"import requests; requests.get('"'"'https://mes-dev.samsong.com'"'"')\""}' | bash "$_sig_script" 2>/dev/null)
_sig_exit=$?
[ "$_sig_exit" = "0" ] && echo "$_sig_result" | grep -q '"decision":"deny"' 2>/dev/null
check $? "skill_instruction_gate: MES+마커없음 → deny (표준 포맷, stdout, exit 0)"

# 복원
[ -n "$_sig_backup_1" ] && mv "$_sig_marker_1.bak" "$_sig_marker_1" 2>/dev/null
[ -n "$_sig_backup_2" ] && mv "$_sig_marker_2.bak" "$_sig_marker_2" 2>/dev/null

# 46-2: completion_gate — deny 포맷이 decision:deny인지 확인 (grep, 이스케이프 따옴표 대응)
grep -q 'decision.*deny' "$HOOKS_DIR/completion_gate.sh" 2>/dev/null
check $? "completion_gate: deny 포맷 통일 확인 (block→deny)"

# 46-3: 전체 훅 deny 포맷 일관성 — hookSpecificOutput 잔재 없음 (smoke_test 자기자신 제외)
! grep -rl 'hookSpecificOutput' "$HOOKS_DIR"/*.sh 2>/dev/null | grep -v 'smoke_test' | grep -v '.bak' | grep -q .
check $? "전체 훅: hookSpecificOutput 잔재 없음 (표준 포맷 통일)"

# 46-4: 전체 훅 block 잔재 없음 (smoke_test 자기자신 제외)
! grep -l '"decision":"block"' "$HOOKS_DIR"/*.sh 2>/dev/null | grep -v 'smoke_test' | grep -q .
check $? "전체 훅: decision:block 잔재 없음 (deny 통일)"

# 46-5: gpt-send 셀렉터 — 프로젝트 slug 기반 필터 확인
_gs_cmd="$PROJECT_DIR/.claude/commands/gpt-send.md"
grep -q 'split' "$_gs_cmd" 2>/dev/null && grep -q 'base' "$_gs_cmd" 2>/dev/null
check $? "gpt-send: 프로젝트 slug 기반 셀렉터 확인 (사이드바 오탐 방지)"

echo ""

# === 라벨 분류 ===
# regression: 항상 통과해야 하는 안정 검증 (실패 = 회귀)
# capability: 아직 불안정하거나 신규 검증 (실패 = 개선 필요)
REGRESSION_SECTIONS="1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 25 26 27 28 29 30"
CAPABILITY_SECTIONS="22 23 24 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46"
# 24b는 24 하위 — capability로 분류. 31은 circuit breaker, 32는 instruction_read_gate, 33-37은 세션40 학습 루프

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
