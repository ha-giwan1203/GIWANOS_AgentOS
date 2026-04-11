#!/bin/bash
# commit_gate.sh — git commit/push 전 자체검증 강제 (PreToolUse/Bash)
# final_check.sh --fast 실패 시 커밋/푸시 차단
# hook 변경 감지 시 --full 자동 승격
# GPT+Claude 합의 2026-04-07

source "$(dirname "$0")/hook_common.sh" 2>/dev/null || true

INPUT=$(cat)
# 안전 JSON 파서 사용 (sed 단독 파싱 취약성 대체, GPT+Claude 합의 2026-04-07)
COMMAND=$(echo "$INPUT" | safe_json_get "command")

# fail-open: 파싱 실패 시 통과 (commit_gate는 차단 목적이 아닌 감지 목적)
# command가 빈 문자열이면 git commit/push가 아니므로 통과
# 주의: JSON 파싱 실패 시에도 COMMAND=""이 되어 게이트 무력화됨
# git commit 또는 git push가 아니면 통과
if ! echo "$COMMAND" | grep -qE 'git (commit|push)'; then
  exit 0
fi

hook_log "PreToolUse/Bash" "commit_gate: git commit/push 감지" 2>/dev/null

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
HOOKS_DIR="$PROJECT_DIR/.claude/hooks"

# hook/settings 변경이 포함된 커밋인지 확인 → --full 승격
MODE="--fast"
STAGED=$(cd "$PROJECT_DIR" && git diff --cached --name-only 2>/dev/null)
if echo "$STAGED" | grep -qE '(\.claude/hooks/|settings.*\.json)'; then
  MODE="--full"
fi

# final_check 실행
RESULT=$(bash "$HOOKS_DIR/final_check.sh" "$MODE" 2>&1)
EXIT_CODE=$?

if [ "$EXIT_CODE" -ne 0 ]; then
  # FAIL 항목만 추출하여 간결한 메시지
  FAILS=$(echo "$RESULT" | grep -E '\[FAIL\]|\[WARN\]' | head -5)
  # 승격 여부 판정
  PROMOTED="false"
  if [ "$MODE" = "--full" ]; then
    PROMOTED="true"
  fi
  # FAIL/WARN 상위 키워드 추출 (최대 3개)
  FAIL_KEYWORDS=$(echo "$RESULT" | grep -oE '\[FAIL\] [^|]+' | head -3 | tr '\n' '; ' | sed 's/; $//')
  WARN_KEYWORDS=$(echo "$RESULT" | grep -oE '\[WARN\] [^|]+' | head -3 | tr '\n' '; ' | sed 's/; $//')
  hook_log "PreToolUse/Bash" "commit_gate BLOCK: final_check $MODE FAIL | promoted=$PROMOTED | fails=$FAIL_KEYWORDS | warns=$WARN_KEYWORDS" 2>/dev/null
  hook_incident "gate_reject" "commit_gate" "" "final_check $MODE FAIL" "\"classification_reason\":\"pre_commit_check\",\"mode\":\"$MODE\",\"promoted_to_full\":$PROMOTED,\"fail_keywords\":\"$FAIL_KEYWORDS\",\"warn_keywords\":\"$WARN_KEYWORDS\",\"next_action\":\"./.claude/hooks/final_check.sh $MODE 를 다시 실행해 FAIL 항목부터 정리\"" 2>/dev/null || true
  echo "{\"decision\":\"deny\",\"reason\":\"[COMMIT GATE] final_check $MODE 실패 — 자체검증 통과 후 커밋하세요.\\n$FAILS\"}"
  exit 0
fi

hook_log "PreToolUse/Bash" "commit_gate PASS: final_check $MODE" 2>/dev/null
exit 0
