#!/bin/bash
# PreToolUse(Bash) hook — 위험 명령 차단 + 보호 경로 삭제/이동 차단
#
# 훅 등급: gate (Phase 2-B 2026-04-19 세션72 명시화)
#   - 차단 메커니즘: JSON `{"hookSpecificOutput":{"permissionDecision":"deny",...}}` (PreToolUse 최신 스펙) + exit 2
#   - timing 계측: hook_timing_start/end 배선
source "$(dirname "$0")/hook_common.sh" 2>/dev/null
_BD_START=$(hook_timing_start)
INPUT=$(cat)
hook_log "PreToolUse/Bash" "block_dangerous 발화"
# 안전 JSON 파서 사용 (sed 단독 파싱 취약성 대체, GPT+Claude 합의 2026-04-07)
COMMAND=$(echo "$INPUT" | safe_json_get "command")

# 0. fail-closed: 파싱 실패 시 통과 금지 (GPT 피드백 2차, 2026-04-07)
if [ -z "$COMMAND" ]; then
  hook_log "PreToolUse/Bash" "WARN: command 파싱 실패 — fail-closed deny"
  echo '{"hookSpecificOutput":{"permissionDecision":"deny","permissionDecisionReason":"[block_dangerous] command 파싱 실패. 입력 확인 필요."}}'
  hook_timing_end "block_dangerous" "$_BD_START" "block_parse"
  exit 2
fi

# 1. 극단 파괴 명령 차단
if echo "$COMMAND" | grep -qE '(rm -rf /|git reset --hard|git clean -fd|git push.*--force.*main)'; then
  echo '{"hookSpecificOutput":{"permissionDecision":"deny","permissionDecisionReason":"위험 명령 차단: 파괴적 명령은 사용자 직접 실행 필요"}}'
  hook_timing_end "block_dangerous" "$_BD_START" "block_destructive"
  exit 2
fi

# 1b. 추가 파괴 패턴 차단 (하네스 강화 Phase 1, GPT 채택)
# tee로 덮어쓰기, cat >로 덮어쓰기, truncate, find -delete, xargs rm
if echo "$COMMAND" | grep -qE '(truncate\s|find\s.*-delete|xargs\s+rm)'; then
  echo '{"hookSpecificOutput":{"permissionDecision":"deny","permissionDecisionReason":"위험 명령 차단: truncate/find -delete/xargs rm은 사용자 직접 실행 필요"}}'
  hook_timing_end "block_dangerous" "$_BD_START" "block_pattern"
  exit 2
fi

# 2. 보호 대상 경로에 대한 삭제/이동/인플레이스 수정 차단
# GPT 합의: "명령어 + 보호 경로" 조합으로만 차단. 임시파일/로그/아카이브 정리는 허용.
# hook_config.json에서 설정 읽기 (Phase 2: 중앙 설정형, fallback: 하드코딩)
CONFIG_FILE="$(dirname "$0")/../hook_config.json"
PROTECTED_PATTERNS='(CLAUDE\.md|README\.md|STATUS\.md|RUNBOOK\.md|AGENTS_GUIDE\.md|settings.*\.json|\.skill|기준정보.*최종)'
DANGER_CMDS='(rm |rm -f |rm -rf |del |Remove-Item |mv |cp |sed -i |tee |cat >|cat >>)'
if [ -f "$CONFIG_FILE" ]; then
  _pp=$(awk '/"protected_path_patterns"/{found=1;next} found && /\]/{exit} found && /"[^"]*"/{gsub(/.*"/, ""); gsub(/".*/, ""); print}' "$CONFIG_FILE" 2>/dev/null | tr '\n' '|' | sed 's/|$//')
  [ -n "$_pp" ] && PROTECTED_PATTERNS="($_pp)"
  _dc=$(awk '/"danger_commands"/{found=1;next} found && /\]/{exit} found && /"[^"]*"/{gsub(/.*"/, ""); gsub(/".*/, ""); print}' "$CONFIG_FILE" 2>/dev/null | tr '\n' '|' | sed 's/|$//')
  [ -n "$_dc" ] && DANGER_CMDS="($_dc)"
fi

# 2b. 보호 경로에 대한 직접 리다이렉션(> file) 차단 (GPT 지적 반영)
if echo "$COMMAND" | grep -qE '>\s*[^|]' 2>/dev/null; then
  if echo "$COMMAND" | grep -qiE "$PROTECTED_PATTERNS"; then
    hook_log "PreToolUse/Bash" "BLOCKED: 보호 경로 리다이렉션 덮어쓰기 — $COMMAND"
    echo '{"hookSpecificOutput":{"permissionDecision":"deny","permissionDecisionReason":"보호 대상 파일 리다이렉션 덮어쓰기 차단. 사용자 직접 실행 필요."}}'
    hook_timing_end "block_dangerous" "$_BD_START" "block_redirect"
    exit 2
  fi
fi

if echo "$COMMAND" | grep -qE "$DANGER_CMDS"; then
  if echo "$COMMAND" | grep -qiE "$PROTECTED_PATTERNS"; then
    hook_log "PreToolUse/Bash" "BLOCKED: 보호 경로 삭제/이동 시도 — $COMMAND"
    echo '{"hookSpecificOutput":{"permissionDecision":"deny","permissionDecisionReason":"보호 대상 파일 삭제/이동 차단. 사용자 직접 실행 필요."}}'
    hook_timing_end "block_dangerous" "$_BD_START" "block_protected"
    exit 2
  fi
fi

# 3. Python heredoc/inline 경유 파일조작 차단 (GPT 실증 시나리오 대응, 2026-04-07)
if echo "$COMMAND" | grep -qE '(python|python3)'; then
  if echo "$COMMAND" | grep -qiE '(os\.(remove|unlink|rename|replace|system)|shutil\.(move|rmtree|copy|copyfile|copy2)|pathlib|Path\(.*\)\.(unlink|rename|replace|write_text|write_bytes)|open\(.+["\x27][waxb]|subprocess\.(run|Popen|call))'; then
    if echo "$COMMAND" | grep -qiE "$PROTECTED_PATTERNS"; then
      hook_log "PreToolUse/Bash" "BLOCKED: Python 경유 보호 파일 조작 시도 — $COMMAND"
      hook_incident "hook_block" "block_dangerous" "" "Python heredoc 보호파일 조작 차단" '"classification_reason":"dangerous_cmd"'
      echo '{"hookSpecificOutput":{"permissionDecision":"deny","permissionDecisionReason":"Python 경유 보호 대상 파일 조작 차단. 사용자 직접 실행 필요."}}'
      hook_timing_end "block_dangerous" "$_BD_START" "block_python"
      exit 2
    fi
  fi
fi

# git commit 감지 → 정합성 검사 리마인드
if echo "$COMMAND" | grep -qE 'git commit'; then
  hook_log "PreToolUse/Bash" "git commit 감지 — /task-status-sync 실행 권장"
fi

hook_timing_end "block_dangerous" "$_BD_START" "pass"
exit 0
