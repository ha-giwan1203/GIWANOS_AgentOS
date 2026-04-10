#!/bin/bash
# PreToolUse Write|Edit|MultiEdit: 작업 전 state 재바인딩
# session_kernel이 없거나 2시간 이상 stale이면 TASKS/HANDOFF 상단을 출력
# → Claude 컨텍스트에 현재 작업 상태를 재주입하는 역할

source "$(dirname "$0")/hook_common.sh"

KERNEL_FILE="$PROJECT_ROOT/.claude/state/session_kernel.md"
REBIND_INTERVAL=7200  # 2시간 (초)

# kernel 없으면 TASKS + HANDOFF 직접 출력
if [ ! -f "$KERNEL_FILE" ]; then
    echo "[state_rebind] ⚠️ session_kernel.md 없음 — 현재 작업 상태를 직접 주입합니다"
    echo "--- TASKS 상단 ---"
    head -20 "$PATH_TASKS" 2>/dev/null
    echo "--- HANDOFF 하단 ---"
    tail -20 "$PATH_HANDOFF" 2>/dev/null
    hook_log "state_rebind_check" "kernel 없음 — TASKS/HANDOFF 직접 출력"
    exit 0
fi

KERNEL_MTIME=$(file_mtime "$KERNEL_FILE")
NOW=$(date +%s)
AGE=$(( NOW - KERNEL_MTIME ))

if [ "$AGE" -gt "$REBIND_INTERVAL" ]; then
    AGE_M=$(( AGE / 60 ))
    echo "[state_rebind] 재바인딩 (${AGE_M}분 경과) — session_kernel 요약:"
    head -25 "$KERNEL_FILE"
    hook_log "state_rebind_check" "stale rebind age=${AGE}s"
else
    # fresh: 로그만 기록, 출력 없음 (컨텍스트 오염 방지)
    hook_log "state_rebind_check" "kernel fresh age=${AGE}s — skip"
fi

exit 0
