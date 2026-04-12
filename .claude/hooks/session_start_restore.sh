#!/bin/bash
# SessionStart hook: startup/resume/compact 시 session_kernel.md 재주입
# 주의: stdout 주입은 버그 가능성 있음 (이슈 #13912, #17550)
# → 파일에 출력 후 경로 안내 방식으로 동작

source "$(dirname "$0")/hook_common.sh"

INPUT=$(cat)
SOURCE=$(printf '%s' "$INPUT" | safe_json_get "source" 2>/dev/null || echo "unknown")
KERNEL_FILE="$PROJECT_ROOT/.claude/state/session_kernel.md"

# evidence 세션 경계 갱신: 새 세션 시작 시 START_FILE 타임스탬프 강제 갱신
# 이전 세션의 .req가 잔존해도 START_FILE이 더 새로우면 evidence_gate가 무시함
SK=$(session_key)
EV_START="$STATE_EVIDENCE/$SK/.session_start"
if [ -d "$STATE_EVIDENCE/$SK" ]; then
  touch "$EV_START"
  hook_log "session_start_restore" "evidence START_FILE refreshed sk=$SK"
fi

hook_log "session_start_restore" "source=$SOURCE"

if [ ! -f "$KERNEL_FILE" ]; then
    echo "[session_start] source=$SOURCE | session_kernel.md 없음 — 첫 세션 또는 PreCompact 미실행"
    exit 0
fi

# kernel 파일 나이 확인
KERNEL_MTIME=$(file_mtime "$KERNEL_FILE")
NOW=$(date +%s)
AGE=$(( NOW - KERNEL_MTIME ))
AGE_H=$(( AGE / 3600 ))

if [ "$AGE" -gt 86400 ]; then
    echo "[session_start] ⚠️ session_kernel.md가 ${AGE_H}시간 전 저장 — stale 가능성. 직접 확인 권장: $KERNEL_FILE"
    hook_log "session_start_restore" "stale kernel age=${AGE}s source=$SOURCE"
    exit 0
fi

# stdout으로 컨텍스트 주입 시도 (best effort — UserPromptSubmit 버그와 유사하게 실패할 수 있음)
# 실패해도 비파괴적. PreToolUse state_rebind_check.sh가 실제 강제선.
echo "=== [session_start: $SOURCE] 이전 세션 상태 ==="
# TASKS 섹션 (12줄)
echo "--- TASKS 상단 ---"
grep -A 12 "^##\? " "$PATH_TASKS" 2>/dev/null | head -12 || head -12 "$PATH_TASKS" 2>/dev/null
# HANDOFF 최신 세션 (상단 20줄 — 최신이 상단)
echo "--- HANDOFF 최신 세션 ---"
head -20 "$PATH_HANDOFF" 2>/dev/null
echo "=== session_kernel 끝 ==="

hook_log "session_start_restore" "kernel 출력 완료 source=$SOURCE age=${AGE}s"
exit 0
