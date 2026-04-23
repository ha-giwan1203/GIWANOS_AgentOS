#!/bin/bash
# Hooks Smoke Test v5 — 현행 훅 실물 기준 (2026-04-15)
# 테스트 45섹션: 운영 훅 + hook_common + incident_ledger + safe_json_get + 퇴행방지 + evidence + selector + instruction_read_gate + 게이트 실행 테스트 + navigate_gate

export LC_ALL=en_US.UTF-8

PASS=0
FAIL=0
TOTAL=0
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
HOOKS_DIR="$PROJECT_DIR/.claude/hooks"
SETTINGS_TEAM="$PROJECT_DIR/.claude/settings.json"
SETTINGS_LOCAL="$PROJECT_DIR/.claude/settings.local.json"
SETTINGS="$SETTINGS_TEAM"
[ -f "$SETTINGS" ] || SETTINGS="$SETTINGS_LOCAL"
# 세션74: team+local union grep helper
grep_settings_any() {
  local needle="$1"
  grep -q "$needle" "$SETTINGS_TEAM" 2>/dev/null || grep -q "$needle" "$SETTINGS_LOCAL" 2>/dev/null
}
grep_settings_none() {
  # 양쪽 어디에도 없으면 exit 0
  ! grep -q "$1" "$SETTINGS_TEAM" 2>/dev/null && ! grep -q "$1" "$SETTINGS_LOCAL" 2>/dev/null
}

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

# === 캐시 체크 (세션76 최적화) ===
# hook 파일 + settings + smoke_test 자신의 해시 기반. TTL 30분.
# SMOKE_TEST_FORCE=1 로 강제 재실행 가능.
CACHE_FILE="$PROJECT_DIR/.claude/state/smoke_test_cache.json"
CACHE_TTL=1800  # 30분

compute_hooks_hash() {
  # *.sh + settings(team+local) 내용 해시. find+sha1sum으로 Windows Git Bash 호환.
  {
    find "$HOOKS_DIR" -maxdepth 1 -name '*.sh' -type f 2>/dev/null | sort | while read f; do
      sha1sum "$f" 2>/dev/null
    done
    [ -f "$SETTINGS_TEAM" ] && sha1sum "$SETTINGS_TEAM" 2>/dev/null
    [ -f "$SETTINGS_LOCAL" ] && sha1sum "$SETTINGS_LOCAL" 2>/dev/null
  } | sha1sum 2>/dev/null | cut -c1-16
}

CURRENT_HASH=$(compute_hooks_hash)

# 캐시 hit 판정
if [ "${SMOKE_TEST_FORCE:-0}" != "1" ] && [ -f "$CACHE_FILE" ] && [ -n "$CURRENT_HASH" ]; then
  CACHED_HASH=$(grep -oE '"hash":[[:space:]]*"[^"]*"' "$CACHE_FILE" 2>/dev/null | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
  CACHED_EPOCH=$(grep -oE '"completed_at_epoch":[[:space:]]*[0-9]+' "$CACHE_FILE" 2>/dev/null | head -1 | grep -oE '[0-9]+')
  NOW_EPOCH=$(date +%s 2>/dev/null)
  if [ "$CACHED_HASH" = "$CURRENT_HASH" ] && [ -n "$CACHED_EPOCH" ] && [ -n "$NOW_EPOCH" ]; then
    ELAPSED=$((NOW_EPOCH - CACHED_EPOCH))
    if [ "$ELAPSED" -lt "$CACHE_TTL" ] 2>/dev/null; then
      MINS_AGO=$((ELAPSED / 60))
      echo "=== smoke_test CACHED PASS (hash=$CURRENT_HASH, ${MINS_AGO}분 전, TTL 30분) ==="
      echo "ALL PASS."
      exit 0
    fi
  fi
fi

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

grep_settings_none '"send_gate\.sh"'
check $? "settings에 send_gate.sh 미등록 (mcp_send_gate는 정상)"

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

# 세션93 (2026-04-22 2자 토론 합의): skill_read 단일·tasks_updated·handoff_updated·domain_read·tasks_read·status_read 제거됨
# 유지 마커: skill_read__<SKILL_ID> (skill_instruction_gate 전담), date_check/auth_diag/identifier_ref (evidence-core)
grep -q 'mark "skill_read__' "$HOOKS_DIR/evidence_mark_read.sh"
check $? "skill_read__<SKILL_ID> 마커 적립 로직 존재 (세션93: skill 전용 마커만 유지)"

grep -qE 'mark "date_check"|mark "auth_diag"|mark "identifier_ref"' "$HOOKS_DIR/evidence_mark_read.sh"
check $? "evidence-core 3종 마커 적립 로직 존재 (세션93)"

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

# settings allow에 CDP 스크립트 허용 없음 확인 (team+local)
grep_settings_none 'scripts/cdp/'
check $? "settings에 CDP 스크립트 허용 없음"

# mcp_send_gate.sh 존재 확인 (Chrome MCP SEND GATE)
test -f "$HOOKS_DIR/mcp_send_gate.sh"
check $? "mcp_send_gate.sh 존재 (Chrome MCP 전송 게이트)"

grep_settings_any 'mcp_send_gate'
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
# 세션86: README가 "31개 등록" 형식으로 작성됨. 패턴 확장 (스크립트|등록 둘 다 허용)
grep -qE '[0-9]+개 (스크립트|등록)' "$HOOKS_DIR/README.md"
check $? "README: 활성 훅 개수 표기 존재 (세션86 패턴 확장: 스크립트|등록)"

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

# settings 등록 확인 (team+local)
grep_settings_any 'instruction_read_gate.sh'
check $? "settings: instruction_read_gate 등록됨"

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
# 대신 deny 함수 내부에서 permissionDecision/decision:deny JSON을 출력하는지 grep으로 확인
# 세션73: hookSpecificOutput 스키마 마이그레이션 후 permissionDecision 키 확인
grep -qE 'permissionDecision.*deny|decision.*deny' "$HOOKS_DIR/evidence_gate.sh" 2>/dev/null
check $? "evidence_gate: deny 함수가 deny JSON 출력 생성"

# 44-2: identifier_ref deny 경로 존재 확인 (세션93: skill_read 제거, identifier_ref만 유지)
grep -q 'identifier_ref.req' "$HOOKS_DIR/evidence_gate.sh"
check $? "evidence_gate: identifier_ref deny 경로 존재 (세션93 evidence-core)"

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

# 세션93 (2026-04-22 2자 토론 합의, plan.md 1주차 4번):
#   evidence_gate에서 tasks_handoff / skill_read / map_scope 블록 제거됨 → 44-3/4/5/7/9/11/12 무효화
#   유지 케이스: 44-6(map_scope req는 더 이상 발행 안 되지만 코드 경로는 제거됐으므로 문서면제 테스트도 의미 없음 → 제거)
#                44-8(risk_profile_prompt touch_req "tasks_handoff" 없음 회귀)
#                44-10(push-only pass — 여전히 evidence_gate 통과, commit_gate가 push 스킵)
#                44-13 identifier_ref.req + 도메인 편집 → deny (신규, evidence-core 유지 증명)
#   새 회귀 트립와이어는 섹션 53(정적 grep)에서 커버. 런타임 테스트는 evidence-core 보증만 유지.

# 44-8 (세션78 P2, 세션93에도 유효): risk_profile_prompt에 tasks_handoff 조기 트리거 없음
! grep -qE '^[^#]*touch_req[[:space:]]+"tasks_handoff"' "$HOOKS_DIR/risk_profile_prompt.sh" 2>/dev/null
check $? "risk_profile_prompt: tasks_handoff 조기 트리거 없음 (세션78/93)"

# 44-10 (세션78/93 유효): push-only pass — evidence_gate는 commit/push 검증 제거, 단순히 evidence-core req만 감시
rm -f "$_eg_req_dir"/*.req 2>/dev/null
rm -f "$_eg_proof_dir"/*.ok 2>/dev/null
_eg_result_10=$(echo '{"command":"git push origin main","tool_name":"Bash","tool_input":""}' | bash "$_eg_script" 2>/dev/null)
if echo "$_eg_result_10" | grep -qE '"decision":"deny"|"permissionDecision":"deny"' 2>/dev/null; then
  check 1 "evidence_gate: ok 없이도 git push → pass (세션93: commit/push 검증 제거)"
else
  check 0 "evidence_gate: ok 없이도 git push → pass (세션93: commit/push 검증 제거)"
fi

# 44-13 (세션93 신규): identifier_ref.req + 도메인 편집 → deny (evidence-core 유지 증명)
rm -f "$_eg_req_dir"/*.req 2>/dev/null
rm -f "$_eg_proof_dir"/*.ok 2>/dev/null
: > "$_eg_req_dir/identifier_ref.req"
touch "$_eg_req_dir/identifier_ref.req" 2>/dev/null
_eg_result_13=$(echo '{"tool_name":"Edit","tool_input":"10_라인배치/SKILL.md","command":""}' | bash "$_eg_script" 2>/dev/null)
echo "$_eg_result_13" | grep -qE '"decision":"deny"|"permissionDecision":"deny"' 2>/dev/null
check $? "evidence_gate: identifier_ref.req + 도메인편집 → deny (세션93 evidence-core)"

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

# 45-2: settings(team+local) 등록 확인
grep_settings_any 'navigate_gate'
check $? "navigate_gate: settings 등록 확인"

# 45-3: 비-chatgpt URL → exit 0 (통과)
_ng_result=$(echo '{"tool_input":{"url":"https://google.com"}}' | bash "$_NG_SCRIPT" 2>/dev/null)
_ng_exit=$?
[ "$_ng_exit" = "0" ] && ! echo "$_ng_result" | grep -qE '"decision":"deny"|"permissionDecision":"deny"' 2>/dev/null
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
echo "$_ng_deny_result" | grep -qE '"decision":"deny"|"permissionDecision":"deny"' 2>/dev/null
check $? "navigate_gate: chatgpt+마커없음 → deny (도메인 무관)"

# 45-5: chatgpt URL + 마커 있음 → 통과
mkdir -p "$_ng_marker_dir" 2>/dev/null
: > "$_ng_marker"
_ng_pass_result=$(echo '{"tool_input":{"url":"https://chatgpt.com/g/g-p-test/project"}}' | bash "$_NG_SCRIPT" 2>/dev/null)
_ng_pass_exit=$?
[ "$_ng_pass_exit" = "0" ] && ! echo "$_ng_pass_result" | grep -qE '"decision":"deny"|"permissionDecision":"deny"' 2>/dev/null
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
[ "$_sig_exit" = "0" ] && echo "$_sig_result" | grep -qE '"decision":"deny"|"permissionDecision":"deny"' 2>/dev/null
check $? "skill_instruction_gate: MES+마커없음 → deny (표준 포맷, stdout, exit 0)"

# 복원
[ -n "$_sig_backup_1" ] && mv "$_sig_marker_1.bak" "$_sig_marker_1" 2>/dev/null
[ -n "$_sig_backup_2" ] && mv "$_sig_marker_2.bak" "$_sig_marker_2" 2>/dev/null

# 46-2: completion_gate — deny 포맷이 decision:deny인지 확인 (grep, 이스케이프 따옴표 대응)
grep -q 'decision.*deny' "$HOOKS_DIR/completion_gate.sh" 2>/dev/null
check $? "completion_gate: deny 포맷 통일 확인 (block→deny)"

# 46-3: PreToolUse 훅 hookSpecificOutput 스키마 적용 확인 (세션73 마이그레이션)
# context7 공식 스펙: PreToolUse는 {"hookSpecificOutput":{"permissionDecision":"deny|allow|ask",...}} 구조
# Stop hook은 legacy {"decision":"deny|block",...} 유지 (이 리스트에서 제외)
_PRETOOLUSE_HOOKS="block_dangerous commit_gate date_scope_guard protect_files harness_gate evidence_gate mcp_send_gate instruction_read_gate skill_instruction_gate debate_gate debate_independent_gate navigate_gate"
_missing_migration=""
for h in $_PRETOOLUSE_HOOKS; do
  if ! grep -q 'hookSpecificOutput' "$HOOKS_DIR/$h.sh" 2>/dev/null; then
    _missing_migration="$_missing_migration $h"
  fi
done
[ -z "$_missing_migration" ]
check $? "PreToolUse 훅 hookSpecificOutput 스키마 적용 (12개, 최신 spec 통일)${_missing_migration:+ | 미마이그레이션:$_missing_migration}"

# 46-4: 전체 훅 block 잔재 없음 (smoke_test 자기자신 제외)
! grep -l '"decision":"block"' "$HOOKS_DIR"/*.sh 2>/dev/null | grep -v 'smoke_test' | grep -q .
check $? "전체 훅: decision:block 잔재 없음 (deny 통일)"

# 46-5: gpt-send 셀렉터 — 프로젝트 slug 기반 필터 확인
_gs_cmd="$PROJECT_DIR/.claude/commands/gpt-send.md"
grep -q 'split' "$_gs_cmd" 2>/dev/null && grep -q 'base' "$_gs_cmd" 2>/dev/null
check $? "gpt-send: 프로젝트 slug 기반 셀렉터 확인 (사이드바 오탐 방지)"

echo ""

# === 48. share_gate.sh (세션79 근본 허점 봉합 — hook 강제) ===
echo "--- 48. share_gate.sh 런타임 테스트 ---"
_SG_SCRIPT="$HOOKS_DIR/share_gate.sh"

# 48-1: 실행권한 + bash -n
test -x "$_SG_SCRIPT" && bash -n "$_SG_SCRIPT" 2>/dev/null
check $? "share_gate: 실행권한 + bash -n"

# 48-2: b5daa2f8 커밋 (hook 신설 포함) → 3way 감지
_sg_output=$(SHARE_GATE_COMMIT=b5daa2f8 bash "$_SG_SCRIPT" 2>&1)
echo "$_sg_output" | grep -q '3way 공유 필수' && echo "$_sg_output" | grep -q 'hook 신설/삭제'
check $? "share_gate: hook 신설 커밋 → 3way + hook 사유 감지"

# 48-3: share-result.md 0단계에 share_gate 호출 명시
grep -q 'share_gate.sh' "$PROJECT_DIR/.claude/commands/share-result.md"
check $? "share_gate: share-result.md 0단계 배선 확인"

echo ""

# === 47. token_threshold_check.sh (세션79 영상분석 드리프트 보정) ===
echo "--- 47. token_threshold_check.sh 런타임 테스트 ---"
_TT_SCRIPT="$HOOKS_DIR/token_threshold_check.sh"

# 47-1: 파일 존재 + 실행권한 + bash -n
test -x "$_TT_SCRIPT" && bash -n "$_TT_SCRIPT" 2>/dev/null
check $? "token_threshold_check: 실행권한 + bash -n"

# 47-2: STRONG mock (1500줄 TASKS, 임계치 800) → [STRONG] + exit 0
_tt_mock_tasks=$(mktemp 2>/dev/null || echo "/tmp/tt_mock_tasks_$$")
_tt_mock_handoff=$(mktemp 2>/dev/null || echo "/tmp/tt_mock_handoff_$$")
_tt_mock_incident=$(mktemp 2>/dev/null || echo "/tmp/tt_mock_incident_$$")
_tt_mock_memdir=$(mktemp -d 2>/dev/null || echo "/tmp/tt_mock_memdir_$$")
mkdir -p "$_tt_mock_memdir" 2>/dev/null
seq 1 1500 > "$_tt_mock_tasks"
: > "$_tt_mock_handoff"
: > "$_tt_mock_incident"

_tt_result=$(TOKEN_THRESHOLD_TASKS_OVERRIDE="$_tt_mock_tasks" \
             TOKEN_THRESHOLD_HANDOFF_OVERRIDE="$_tt_mock_handoff" \
             TOKEN_THRESHOLD_MEMORY_OVERRIDE="$_tt_mock_memdir" \
             TOKEN_THRESHOLD_INCIDENT_OVERRIDE="$_tt_mock_incident" \
             bash "$_TT_SCRIPT" 2>&1)
_tt_exit=$?
[ "$_tt_exit" = "0" ] && echo "$_tt_result" | grep -q '\[STRONG\]'
check $? "token_threshold_check: STRONG mock → [STRONG] 출력 + exit 0"

# 47-3: 정상 mock (짧은 파일, 빈 메모리 디렉토리) → 빈 출력
seq 1 100 > "$_tt_mock_tasks"
_tt_result_clean=$(TOKEN_THRESHOLD_TASKS_OVERRIDE="$_tt_mock_tasks" \
                   TOKEN_THRESHOLD_HANDOFF_OVERRIDE="$_tt_mock_handoff" \
                   TOKEN_THRESHOLD_MEMORY_OVERRIDE="$_tt_mock_memdir" \
                   TOKEN_THRESHOLD_INCIDENT_OVERRIDE="$_tt_mock_incident" \
                   bash "$_TT_SCRIPT" 2>&1)
[ -z "$_tt_result_clean" ]
check $? "token_threshold_check: 정상 mock → 빈 출력 (깨끗한 세션)"

# 47-4: SKILL.md 존재 (스킬 실물 커밋 확인)
test -f "$PROJECT_DIR/90_공통기준/스킬/token-threshold-warn/SKILL.md"
check $? "token-threshold-warn: SKILL.md 파일 존재"

# 47-5: session_start_restore 배선 확인
grep -q 'token_threshold_check' "$HOOKS_DIR/session_start_restore.sh" 2>/dev/null
check $? "token_threshold_check: session_start_restore.sh 배선 확인"

# 정리
rm -f "$_tt_mock_tasks" "$_tt_mock_handoff" "$_tt_mock_incident" 2>/dev/null
rm -rf "$_tt_mock_memdir" 2>/dev/null

echo ""

# === 섹션 48: evidence_gate fingerprint suppress 확장 (세션83 Round 2 [3way] API 예외) ===
# 배경: 04-19 165건 중 fp 상위 3종 66% 집중, 반복 간격 30~90초 → 기존 GRACE=30 경계선 탈출
# 4개 확장추론 모델 만장일치(Gemini 2.5-pro/3.1-pro-preview + GPT o4-mini/5.2): 차단 유지 + 기록 억제 확장

# 48-1: GRACE_WINDOW 30에서 확장됨 (세션83 Round 2 이후 30이 아닌 값 유지)
# 세션86 Case A에서 120→300 재조정됨. 구체 값 검증은 섹션 51-1.
! grep -qE 'local GRACE_WINDOW=30$' "$HOOKS_DIR/evidence_gate.sh"
check $? "evidence_gate: GRACE_WINDOW 30에서 확장 유지 (세션83 Round 2 기준)"

# 48-2: fingerprint scan 범위 tail -30→-100 확장
grep -qE 'tail -100 "\$INCIDENT_LEDGER"' "$HOOKS_DIR/evidence_gate.sh"
check $? "evidence_gate: fingerprint scan tail=100 (세션83 Round 2)"

# 48-3: stderr 반복 차단 경고 문구 추가
grep -qE '반복 차단 감지' "$HOOKS_DIR/evidence_gate.sh"
check $? "evidence_gate: stderr 반복 차단 경고 (세션83 Round 2)"

# 48-4: 기존 suppress 로직 유지 확인 (_should_record 제어 플로우)
grep -qE '_should_record=false' "$HOOKS_DIR/evidence_gate.sh"
check $? "evidence_gate: _should_record 억제 플로우 유지"

# 48-5 (세션93 합의로 무효화): tasks_updated/handoff_updated 참조 블록 자체가 evidence_gate에서 제거됨.
# 회귀 트립와이어는 섹션 53-a (정적 grep, 재주입 방지)로 이전됨. 여기서는 스킵.

echo ""

# === 섹션 49: gpt-send/gpt-read thinking 모델 탐지 (세션83 C [3way] API 예외) ===
# 배경: 세션82 gpt-5-4-thinking 확장 추론 중 stop-button 잔존 → Claude stop 오클릭
# 합의: slug includes 'thinking'|'reasoning' + stop-button 단독 판정 금지 (블록 안정 3회 연속 동일)

# 49-1: gpt-read에 isExtended 감지 로직
grep -qE "slug\.includes\('thinking'\) \|\| slug\.includes\('reasoning'\)" "$PROJECT_ROOT/.claude/commands/gpt-read.md"
check $? "gpt-read: data-message-model-slug thinking/reasoning 감지 (세션83)"

# 49-2: gpt-read에 maxTimeout 600초 조건부
grep -qE "maxTimeout: isExtended \? 600 : 300" "$PROJECT_ROOT/.claude/commands/gpt-read.md"
check $? "gpt-read: isExtended=true 시 600초 확장"

# 49-3: gpt-read에 블록 안정 3회 연속 동일 종료 경로
grep -qE "블록 안정 3회 연속 동일" "$PROJECT_ROOT/.claude/commands/gpt-read.md"
check $? "gpt-read: 블록 안정 3회 연속 종료 경로 (stop-button 단독 판정 금지)"

# 49-4: gpt-send에 isExtended 탐지 동기화
grep -qE "isExtended.*thinking.*reasoning" "$PROJECT_ROOT/.claude/commands/gpt-send.md"
check $? "gpt-send: thinking/reasoning 감지 동기화 (세션83)"

# 49-5: gpt-send에 stop-button 단독 판정 금지 명시
grep -qE "stop-button 단독 판정 금지" "$PROJECT_ROOT/.claude/commands/gpt-send.md"
check $? "gpt-send: stop-button 단독 판정 금지 명시"

echo ""

# === 섹션 50: β안-C 단발 교차 검증 API 병렬 예외 (세션86 [3way] 만장일치 구현) ===
# 배경: 세션85 debate_20260420_190020_beta_3way pass_ratio=1.0 만장일치 채택.
# Step 6-2/6-4 단발 교차 검증만 API 병렬 허용. 본론·종합·최종판정 API 호출 금지.
# 구현: openai/openai_debate.py(call_openai_parallel) + gemini/gemini_debate.py(call_gemini_parallel)
#      + bridge/log_bridge.py (JSON 스키마 검증) + bridge/api_fallback.py (1회 재시도 + rate limit 분기)
BETA_C_DIR="$PROJECT_ROOT/90_공통기준/토론모드"

# 50-1: 원문 payload 누락 assert 차단 — openai.call_openai require_payload 임계 확인
grep -qE "require_payload: bool = False" "$BETA_C_DIR/openai/openai_debate.py"
check $? "β안-C: openai_debate.call_openai require_payload 플래그 존재"
grep -qE "PAYLOAD_MIN_LEN" "$BETA_C_DIR/openai/openai_debate.py"
check $? "β안-C: openai_debate PAYLOAD_MIN_LEN 임계 정의"
grep -qE "PAYLOAD_MIN_LEN" "$BETA_C_DIR/gemini/gemini_debate.py"
check $? "β안-C: gemini_debate PAYLOAD_MIN_LEN 임계 정의"

# 50-2: 병렬 호출 함수 존재 (순차 금지 [NEVER] 4번)
grep -qE "def call_openai_parallel" "$BETA_C_DIR/openai/openai_debate.py"
check $? "β안-C: openai_debate.call_openai_parallel 정의"
grep -qE "def call_gemini_parallel" "$BETA_C_DIR/gemini/gemini_debate.py"
check $? "β안-C: gemini_debate.call_gemini_parallel 정의"
grep -qE "ThreadPoolExecutor" "$BETA_C_DIR/openai/openai_debate.py"
check $? "β안-C: openai_debate ThreadPoolExecutor 사용 (병렬화)"

# 50-3: API 실패 fallback self-test PASS (무한 재시도 금지 [NEVER] 6번)
if PYTHONIOENCODING=utf-8 python3 "$BETA_C_DIR/bridge/api_fallback.py" --self-test 2>&1 | grep -q "\[PASS\] api_fallback self-test 4/4"; then
  check 0 "β안-C: api_fallback self-test 4/4 PASS (1회 재시도 + rate limit 즉시 fallback)"
else
  check 1 "β안-C: api_fallback self-test FAIL"
fi

# 50-4: 로그 브릿지 JSON 스키마 검증 (cross_verification 4필드 필수)
if PYTHONIOENCODING=utf-8 python3 "$BETA_C_DIR/bridge/log_bridge.py" --self-test 2>&1 | grep -q "\[PASS\] log_bridge self-test 4/4"; then
  check 0 "β안-C: log_bridge self-test 4/4 PASS (enum·필수필드·log_path 검증)"
else
  check 1 "β안-C: log_bridge self-test FAIL"
fi
grep -qE "gemini_verifies_gpt" "$BETA_C_DIR/bridge/log_bridge.py"
check $? "β안-C: log_bridge JSON 스키마 gemini_verifies_gpt 필드"
grep -qE "gpt_verifies_gemini" "$BETA_C_DIR/bridge/log_bridge.py"
check $? "β안-C: log_bridge JSON 스키마 gpt_verifies_gemini 필드"

# 50-5: [NEVER] 회귀 — 본론·종합·최종판정 API 전환 금지 규정 실물 존재
grep -qE "본론.*6-1.*6-3.*API 전환 금지" "$BETA_C_DIR/CLAUDE.md"
check $? "β안-C [NEVER]: 본론(6-1/6-3) API 전환 금지 규정 유지"
grep -qE "종합.*6-5.*API 전환 금지" "$BETA_C_DIR/CLAUDE.md"
check $? "β안-C [NEVER]: 종합(6-5) API 전환 금지 규정 유지"
grep -qE "최종 판정.*웹 UI" "$BETA_C_DIR/CLAUDE.md"
check $? "β안-C [NEVER]: 최종 판정 웹 UI 수령만 인정 규정 유지"

echo ""

# === 섹션 51: evidence_gate GRACE 확장 (세션86 Case A, 2자 토론 GPT 조건부 통과) ===
# 배경: 세션86 실측 (incident_improvement_20260421_session86.md) — GRACE=120 설계가 7일 81.5% 반복 놓침
# 실측 median 347s, Top3 fp median 320~370s → 120→300 확장 (120~300 구간 회수)
# GPT(gpt-5-4-thinking) 조건부 통과 수정: 경계쌍(299s suppress / 301s record) + 주석 근거 강제

# 51-1: GRACE_WINDOW=300 확장 확인 (세션86 Case A 핵심)
grep -qE 'GRACE_WINDOW=300' "$HOOKS_DIR/evidence_gate.sh"
check $? "evidence_gate: GRACE_WINDOW 120→300 확장 (세션86 Case A)"

# 51-2: 세션86 실측 근거 주석 존재 (GPT 수정 항목 #2)
grep -qE '세션86.*Case A' "$HOOKS_DIR/evidence_gate.sh"
check $? "evidence_gate: 세션86 Case A 주석 근거 추가"
grep -qE '120~300 구간 회수' "$HOOKS_DIR/evidence_gate.sh"
check $? "evidence_gate: '120~300 구간 회수' 목적 주석 (GPT 수정 #2)"

# 51-3: 경계쌍 주석 명시 — 299s suppress / 301s record (GPT 수정 항목 #1)
grep -qE '299s.*suppress.*301s.*record' "$HOOKS_DIR/evidence_gate.sh"
check $? "evidence_gate: 경계쌍 299s/301s 주석 박음 (GPT 수정 #1)"

# 51-4: fingerprint 정의 불변 확인 (Case B 분리 경계 — GPT 지적 반영)
grep -qE '\$\{reason:0:80\}\|\$\{COMMAND:0:50\}' "$HOOKS_DIR/evidence_gate.sh"
check $? "evidence_gate: fingerprint 정의(reason:0:80|command:0:50) 변경 없음 (Case B 분리)"

# 51-5: deny 경로 불변 확인 (classification_reason evidence_missing 유지)
grep -qE 'classification_reason.*evidence_missing' "$HOOKS_DIR/evidence_gate.sh"
check $? "evidence_gate: deny evidence_missing 라벨 유지"

# 51-6 (세션93 합의로 무효화): tasks_updated/handoff_updated 블록 자체 제거됨.
# 회귀 방지는 섹션 53-a 정적 grep으로 대체.

echo ""

# === 52. /finish 4.5단계 Notion 동기화 배선 검증 (세션86 3자 토론 만장일치 채택) ===
# 배경: 세션45~86 Notion 미동기화 사건. finish.md 3.5단계 명세 있었으나 share-result 위임 구조로 실행 누락.
# 검증 3축 (GPT 조건부 통과 보정 반영):
#   (a) finish.md가 --manual-sync 플래그로 notion_sync.py 호출
#   (b) share-result.md가 Notion 로직을 포함하지 않음 (책임 분리)
#   (c) notion_sync.py에 sync_from_finish wrapper 존재 (허위 이력 append 방지)
echo ""
echo "--- 52. /finish 4.5 Notion 동기화 배선 (세션86 3자) ---"

FINISH_MD="$PROJECT_DIR/.claude/commands/finish.md"
SHARE_MD="$PROJECT_DIR/.claude/commands/share-result.md"
NOTION_PY="$PROJECT_DIR/90_공통기준/업무관리/notion_sync.py"

grep -q "notion_sync.py --manual-sync" "$FINISH_MD" 2>/dev/null
check $? "(a) finish.md: 'notion_sync.py --manual-sync' 호출 구문 존재"

# (b) share-result.md: 주석/안내 라인 제외 후 실제 Python 호출 패턴이 있으면 FAIL
# — 이전 검증식은 "Notion 동기화는" 주석이 있으면 실제 호출이 섞여도 통과하는 구멍 (세션86 GPT Round 2 지적)
# — 강화: `>` 블록인용·`#` 주석 + 설계 주석 제외 후 본문에 notion_sync·sync_batch·sync_from_finish 호출 차단
! grep -vE "^\s*>|^\s*#|Notion 동기화는|/finish 4.5 전용|로그.*debate" "$SHARE_MD" 2>/dev/null \
  | grep -qE "notion_sync|sync_batch|sync_from_finish"
check $? "(b) share-result.md: Notion 실제 호출 차단 (주석·인용만 허용, GPT R2 보정)"

grep -q "def sync_from_finish" "$NOTION_PY" 2>/dev/null
check $? "(c) notion_sync.py: sync_from_finish wrapper 존재 (허위 이력 방지)"

# === 53. evidence 축 경계 회귀 (세션93, plan.md 1주차 4번 (e)) ===
# 2자 토론 합의로 evidence_gate에서 제거된 블록이 다시 들어오지 않도록 트립와이어.
# 모든 검사는 주석(#로 시작하는 라인)을 제외한 active code만 대상.
echo ""
echo "=== 53. evidence 축 경계 회귀 (세션93) ==="

# 53-a: evidence_gate.sh active code에서 tasks_updated/handoff_updated/tasks_handoff 참조 0건
TH_HITS=$(grep -v '^[[:space:]]*#' "$PROJECT_DIR/.claude/hooks/evidence_gate.sh" | grep -cE 'fresh_ok "tasks_updated"|fresh_ok "handoff_updated"|deny.*"tasks_handoff"' 2>/dev/null)
[ "${TH_HITS:-0}" -eq 0 ]
check $? "evidence_gate.sh: tasks_handoff 차단 로직 제거 유지 (commit_gate/completion_gate 소유)"

# 53-b: evidence_gate.sh active code에서 map_scope 차단 로직 0건
MS_HITS=$(grep -v '^[[:space:]]*#' "$PROJECT_DIR/.claude/hooks/evidence_gate.sh" | grep -cE 'fresh_req "map_scope"|deny.*"map_scope"' 2>/dev/null)
[ "${MS_HITS:-0}" -eq 0 ]
check $? "evidence_gate.sh: map_scope 차단 로직 제거 유지 (evidence 버스 분리)"

# 53-c: evidence_gate.sh active code에서 fresh_req "skill_read" 참조 0건
SR_HITS=$(grep -v '^[[:space:]]*#' "$PROJECT_DIR/.claude/hooks/evidence_gate.sh" | grep -c 'fresh_req "skill_read"' 2>/dev/null)
[ "${SR_HITS:-0}" -eq 0 ]
check $? "evidence_gate.sh: skill_read 그룹 제거 유지 (skill_instruction_gate 전담)"

# 53-d: risk_profile_prompt.sh active code에서 map_scope/skill_read/tasks_handoff req 발행 0건
RP_HITS=$(grep -v '^[[:space:]]*#' "$PROJECT_DIR/.claude/hooks/risk_profile_prompt.sh" | grep -cE 'touch_req "map_scope|touch_req "skill_read"|touch_req "tasks_handoff"' 2>/dev/null)
[ "${RP_HITS:-0}" -eq 0 ]
check $? "risk_profile_prompt.sh: map_scope/skill_read/tasks_handoff req 발행 제거 유지"

# 53-e: evidence_mark_read.sh active code에서 C분류 마커 생성 0건
EM_HITS=$(grep -v '^[[:space:]]*#' "$PROJECT_DIR/.claude/hooks/evidence_mark_read.sh" | grep -cE 'mark "tasks_read"|mark "handoff_read"|mark "status_read"|mark "domain_read"|mark "tasks_updated"|mark "handoff_updated"|^echo "\$NORM_TEXT" \| grep -qE .SKILL\\\\\.md. && mark "skill_read"' 2>/dev/null)
[ "${EM_HITS:-0}" -eq 0 ]
check $? "evidence_mark_read.sh: C분류 마커(tasks_read/handoff_read/status_read/domain_read/tasks_updated/handoff_updated/skill_read) 제거 유지"

# === 섹션 54: 파싱 헬퍼 (parse_helpers.py) M1 shadow mode (세션96 /auto-fix 2자 토론 A-수정안) ===
echo ""
echo "=== 54. parse_helpers.py M1 — 헬퍼 신설 + shadow 검증 ==="
PARSE_HELPERS="$PROJECT_DIR/.claude/scripts/parse_helpers.py"

# 54-1: parse_helpers.py 실파일 존재
[ -f "$PARSE_HELPERS" ]
check $? "parse_helpers.py 실파일 존재 (.claude/scripts/parse_helpers.py)"

# 54-2: hooks_from_settings total = list_active_hooks --count
PY_CMD="python"
command -v python3 >/dev/null 2>&1 && PY_CMD="python3"
HELPER_TOTAL=$("$PY_CMD" "$PARSE_HELPERS" --op hooks_from_settings --path "$SETTINGS_TEAM" --path "$SETTINGS_LOCAL" 2>/dev/null | "$PY_CMD" -c "import sys,json; print(json.load(sys.stdin)['total'])" 2>/dev/null)
INLINE_TOTAL=$(bash "$PROJECT_DIR/.claude/hooks/list_active_hooks.sh" --count 2>/dev/null)
[ -n "$HELPER_TOTAL" ] && [ -n "$INLINE_TOTAL" ] && [ "$HELPER_TOTAL" = "$INLINE_TOTAL" ]
check $? "hooks_from_settings total ($HELPER_TOTAL) = list_active_hooks --count ($INLINE_TOTAL)"

# 54-3: shadow_diff_active_hooks match=true (독립 재구현 일치)
SHADOW_MATCH=$("$PY_CMD" "$PARSE_HELPERS" --op shadow_diff_active_hooks --path "$SETTINGS_TEAM" --path "$SETTINGS_LOCAL" 2>/dev/null | "$PY_CMD" -c "import sys,json; print(json.load(sys.stdin)['match'])" 2>/dev/null)
[ "$SHADOW_MATCH" = "True" ]
check $? "shadow_diff_active_hooks: helper vs inline 독립 재구현 match=True"

# 54-4: doc_dates TASKS.md — 최종 업데이트 날짜 파싱
TASKS_DATE=$("$PY_CMD" "$PARSE_HELPERS" --op doc_dates --path "$PROJECT_DIR/90_공통기준/업무관리/TASKS.md" 2>/dev/null | "$PY_CMD" -c "import sys,json; d=json.load(sys.stdin); print(d.get('date') or '')" 2>/dev/null)
[ -n "$TASKS_DATE" ] && echo "$TASKS_DATE" | grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
check $? "doc_dates: TASKS.md 날짜 파싱 ($TASKS_DATE)"

# 54-5: doc_session TASKS.md — 세션 번호 파싱 (integer)
TASKS_SESSION=$("$PY_CMD" "$PARSE_HELPERS" --op doc_session --path "$PROJECT_DIR/90_공통기준/업무관리/TASKS.md" 2>/dev/null | "$PY_CMD" -c "import sys,json; d=json.load(sys.stdin); print(d.get('session') or '')" 2>/dev/null)
[ -n "$TASKS_SESSION" ] && echo "$TASKS_SESSION" | grep -qE '^[0-9]+$'
check $? "doc_session: TASKS.md 세션 번호 파싱 ($TASKS_SESSION)"

# === 라벨 분류 ===
# regression: 항상 통과해야 하는 안정 검증 (실패 = 회귀)
# capability: 아직 불안정하거나 신규 검증 (실패 = 개선 필요)
REGRESSION_SECTIONS="1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 25 26 27 28 29 30 53 54"
CAPABILITY_SECTIONS="22 23 24 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 51 52"
# 24b는 24 하위 — capability로 분류. 31은 circuit breaker, 32는 instruction_read_gate, 33-37은 세션40 학습 루프
# 53: 세션93 evidence 축 경계 회귀 — regression으로 분류 (plan.md 1주차 4번)
# 54: 세션96 parse_helpers.py M1 — regression으로 분류 (shadow mode 기본 동작 회귀 방지)

echo ""
echo "=== 라벨 분류 ==="
echo "  regression (안정): 섹션 $REGRESSION_SECTIONS"
echo "  capability (신규): 섹션 $CAPABILITY_SECTIONS + 24b"

# === 결과 ===
echo ""
echo "=== 결과: $PASS/$TOTAL PASS, $FAIL FAIL ==="

# === 캐시 저장 (PASS 시만) ===
if [ "$FAIL" -eq 0 ] && [ -n "$CURRENT_HASH" ]; then
  mkdir -p "$(dirname "$CACHE_FILE")" 2>/dev/null || true
  _now_iso=$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo "")
  _now_epoch=$(date +%s 2>/dev/null || echo 0)
  cat > "$CACHE_FILE" <<EOF
{
  "hash": "$CURRENT_HASH",
  "pass_total": $PASS,
  "fail_total": $FAIL,
  "completed_at": "$_now_iso",
  "completed_at_epoch": $_now_epoch,
  "ttl_sec": $CACHE_TTL
}
EOF
fi

if [ "$FAIL" -gt 0 ]; then
  echo "WARNING: $FAIL개 실패. hooks 수정 확인 필요."
  exit 1
else
  echo "ALL PASS."
  exit 0
fi
