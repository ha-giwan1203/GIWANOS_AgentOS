#!/bin/bash
# PreToolUse(Bash) hook — 위험 명령 차단 + 보호 경로 삭제/이동 차단
source "$(dirname "$0")/hook_common.sh" 2>/dev/null
INPUT=$(cat)
hook_log "PreToolUse/Bash" "block_dangerous 발화"
# 안전 JSON 파서 사용 (sed 단독 파싱 취약성 대체, GPT+Claude 합의 2026-04-07)
COMMAND=$(echo "$INPUT" | safe_json_get "command")

# 1. 극단 파괴 명령 차단
if echo "$COMMAND" | grep -qE '(rm -rf /|git reset --hard|git clean -fd|git push.*--force.*main)'; then
  echo '{"decision":"deny","reason":"위험 명령 차단: 파괴적 명령은 사용자 직접 실행 필요"}'
  exit 0
fi

# 2. 보호 대상 경로에 대한 삭제/이동/인플레이스 수정 차단
# GPT 합의: "명령어 + 보호 경로" 조합으로만 차단. 임시파일/로그/아카이브 정리는 허용.
PROTECTED_PATTERNS='(CLAUDE\.md|README\.md|STATUS\.md|RUNBOOK\.md|AGENTS_GUIDE\.md|settings.*\.json|\.skill|기준정보.*최종)'
DANGER_CMDS='(rm |rm -f |rm -rf |del |Remove-Item |mv |cp |sed -i )'

if echo "$COMMAND" | grep -qE "$DANGER_CMDS"; then
  if echo "$COMMAND" | grep -qiE "$PROTECTED_PATTERNS"; then
    hook_log "PreToolUse/Bash" "BLOCKED: 보호 경로 삭제/이동 시도 — $COMMAND"
    echo '{"decision":"deny","reason":"보호 대상 파일 삭제/이동 차단. 사용자 직접 실행 필요."}'
    exit 0
  fi
fi

# 3. Python heredoc/inline 경유 파일조작 차단 (GPT 실증 시나리오 대응, 2026-04-07)
if echo "$COMMAND" | grep -qE '(python|python3)'; then
  if echo "$COMMAND" | grep -qiE '(os\.remove|os\.unlink|shutil\.(move|rmtree|copy)|open\(.+["\x27]w)'; then
    if echo "$COMMAND" | grep -qiE "$PROTECTED_PATTERNS"; then
      hook_log "PreToolUse/Bash" "BLOCKED: Python 경유 보호 파일 조작 시도 — $COMMAND"
      hook_incident "hook_block" "block_dangerous" "" "Python heredoc 보호파일 조작 차단"
      echo '{"decision":"deny","reason":"Python 경유 보호 대상 파일 조작 차단. 사용자 직접 실행 필요."}'
      exit 0
    fi
  fi
fi

# git commit 감지 → 정합성 검사 리마인드
if echo "$COMMAND" | grep -qE 'git commit'; then
  hook_log "PreToolUse/Bash" "git commit 감지 — /task-status-sync 실행 권장"
fi
