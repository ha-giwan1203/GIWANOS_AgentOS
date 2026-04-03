#!/bin/bash
# PreToolUse(Bash) hook — 위험 명령 차단 + 커밋 전 정합성 알림
source "$(dirname "$0")/hook_common.sh" 2>/dev/null
INPUT=$(cat)
hook_log "PreToolUse/Bash" "block_dangerous 발화"
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

# 차단 패턴
if echo "$COMMAND" | grep -qE '(rm -rf /|git reset --hard|git clean -fd|git push.*--force.*main)'; then
  echo '{"decision":"deny","reason":"위험 명령 차단: 파괴적 명령은 사용자 직접 실행 필요"}'
  exit 0
fi

# git commit 감지 → 정합성 검사 리마인드
if echo "$COMMAND" | grep -qE 'git commit'; then
  echo "[Hook] git commit 감지. /task-status-sync 실행 여부 확인 권장." >> "$HOME/Desktop/업무리스트/.claude/hooks/hook_log.txt"
fi
