#!/bin/bash
# PreCompact hook: compact 직전 session_kernel.md에 현재 상태 저장
# auto-compact / manual compact 모두 트리거됨 (v1.0.48+)

source "$(dirname "$0")/hook_common.sh"

TIMESTAMP=$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M KST' 2>/dev/null || date '+%Y-%m-%d %H:%M')
STATE_DIR="$PROJECT_ROOT/.claude/state"
KERNEL_FILE="$STATE_DIR/session_kernel.md"

mkdir -p "$STATE_DIR"

# TASKS.md 상단 35줄 (현재 의제)
TASKS_EXCERPT=$(head -35 "$PATH_TASKS" 2>/dev/null || echo "(TASKS.md 없음)")

# HANDOFF.md 하단 50줄 (최신 상태)
HANDOFF_EXCERPT=$(tail -50 "$PATH_HANDOFF" 2>/dev/null || echo "(HANDOFF.md 없음)")

cat > "$KERNEL_FILE" << KERNEL
# Session Kernel (PreCompact 저장: $TIMESTAMP)
> compact 후 세션 재개 시 자동 로드. 직접 편집 금지 — precompact_save.sh가 덮어씀.

## TASKS 현재 의제 (상단 35줄)
$TASKS_EXCERPT

## HANDOFF 현재 상태 (하단 50줄)
$HANDOFF_EXCERPT
KERNEL

hook_log "precompact_save" "session_kernel 저장 완료: $TIMESTAMP"
echo "[precompact_save] session_kernel.md 저장 완료 ($TIMESTAMP)" >&2
exit 0
