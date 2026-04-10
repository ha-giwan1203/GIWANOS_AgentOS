#!/bin/bash
# SessionStart hook: startup/resume/compact 시 session_kernel.md 재주입
# 주의: stdout 주입은 버그 가능성 있음 (이슈 #13912, #17550)
# → 파일에 출력 후 경로 안내 방식으로 동작

source "$(dirname "$0")/hook_common.sh"

INPUT=$(cat)
SOURCE=$(printf '%s' "$INPUT" | safe_json_get "source" 2>/dev/null || echo "unknown")
KERNEL_FILE="$PROJECT_ROOT/.claude/state/session_kernel.md"

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

# stdout으로 컨텍스트 주입 시도 (버그 있으면 무시됨 — 비파괴적)
echo "=== [session_start: $SOURCE] 이전 세션 상태 (session_kernel.md) ==="
cat "$KERNEL_FILE"
echo "=== session_kernel 끝 ==="

hook_log "session_start_restore" "kernel 출력 완료 source=$SOURCE age=${AGE}s"
exit 0
