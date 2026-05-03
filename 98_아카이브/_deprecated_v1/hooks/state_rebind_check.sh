#!/bin/bash
# PreToolUse Write|Edit|MultiEdit: 작업 전 state 재바인딩
# - session_kernel이 없거나 1시간 이상 stale이면 TASKS/HANDOFF 섹션별로 짧게 재주입
# - last_rebind_at stamp로 한 번 stale 후 반복 출력 방지 (30분 간격)

source "$(dirname "$0")/hook_common.sh"
# 훅 등급: advisory (Phase 2-C 2026-04-19 세션73 timing 배선)
_SRC_START=$(hook_timing_start)

KERNEL_FILE="$PROJECT_ROOT/.claude/state/session_kernel.md"
REBIND_INTERVAL=3600      # 1시간: kernel 기준 stale 판정
REBIND_COOLDOWN=1800      # 30분: 재주입 반복 방지 (last_rebind_at 갱신 간격)
REBIND_STAMP="$PROJECT_ROOT/.claude/state/last_rebind_at"

NOW=$(date +%s)

# ── last_rebind_at 쿨다운 확인 ──────────────────────────────
if [ -f "$REBIND_STAMP" ]; then
    LAST_REBIND=$(cat "$REBIND_STAMP" 2>/dev/null || echo 0)
    SINCE_REBIND=$(( NOW - LAST_REBIND ))
    if [ "$SINCE_REBIND" -lt "$REBIND_COOLDOWN" ]; then
        hook_log "state_rebind_check" "cooldown skip since_rebind=${SINCE_REBIND}s"
        hook_timing_end "state_rebind_check" "$_SRC_START" "skip_cooldown"
        exit 0
    fi
fi

# ── session_kernel 없으면 TASKS+HANDOFF 직접 출력 ──────────
if [ ! -f "$KERNEL_FILE" ]; then
    echo "[state_rebind] ⚠️ session_kernel.md 없음 — 현재 작업 상태 직접 주입"
    echo "--- TASKS 상단 15줄 ---"
    head -15 "$PATH_TASKS" 2>/dev/null
    echo "--- HANDOFF 상단 20줄 ---"
    head -20 "$PATH_HANDOFF" 2>/dev/null
    echo "$NOW" > "$REBIND_STAMP"
    hook_log "state_rebind_check" "kernel 없음 — TASKS/HANDOFF 직접 출력"
    hook_timing_end "state_rebind_check" "$_SRC_START" "rebind_nokernel"
    exit 0
fi

# ── kernel stale 여부 확인 ──────────────────────────────────
KERNEL_MTIME=$(file_mtime "$KERNEL_FILE")
AGE=$(( NOW - KERNEL_MTIME ))

if [ "$AGE" -gt "$REBIND_INTERVAL" ]; then
    AGE_M=$(( AGE / 60 ))
    echo "[state_rebind] 재바인딩 (kernel ${AGE_M}분 경과)"
    # TASKS 섹션 (12줄)
    echo "--- TASKS 상단 ---"
    head -12 "$PATH_TASKS" 2>/dev/null
    # HANDOFF 최신 세션 섹션 (상단 20줄, 최신이 상단)
    echo "--- HANDOFF 최신 세션 ---"
    head -20 "$PATH_HANDOFF" 2>/dev/null
    echo "$NOW" > "$REBIND_STAMP"
    hook_log "state_rebind_check" "stale rebind age=${AGE}s"
    hook_timing_end "state_rebind_check" "$_SRC_START" "rebind_stale"
else
    hook_log "state_rebind_check" "kernel fresh age=${AGE}s — skip"
    hook_timing_end "state_rebind_check" "$_SRC_START" "skip_fresh"
fi

exit 0
