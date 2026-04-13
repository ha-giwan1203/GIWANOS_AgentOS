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

# instruction_reads 세션 초기화: 이전 세션의 읽기 마커 무효화
INSTRUCTION_DIR="$PROJECT_ROOT/.claude/state/instruction_reads"
if [ -d "$INSTRUCTION_DIR" ]; then
  rm -f "$INSTRUCTION_DIR"/*.ok 2>/dev/null
  hook_log "session_start_restore" "instruction_reads cleared"
fi

hook_log "session_start_restore" "source=$SOURCE"

# hook_config.json에서 설정 읽기 (Phase 2: 중앙 설정형)
CONFIG_FILE="$PROJECT_ROOT/.claude/hook_config.json"
STALE_HOURS=24
FALLBACK_TASKS_LINES=20
FALLBACK_HANDOFF_LINES=20
if [ -f "$CONFIG_FILE" ]; then
  _h=$(grep '"kernel_stale_threshold_hours"' "$CONFIG_FILE" 2>/dev/null | sed 's/[^0-9]//g' | head -1)
  [ -n "$_h" ] && STALE_HOURS="$_h"
  _t=$(grep '"fallback_tasks_lines"' "$CONFIG_FILE" 2>/dev/null | sed 's/[^0-9]//g' | head -1)
  [ -n "$_t" ] && FALLBACK_TASKS_LINES="$_t"
  _hf=$(grep '"fallback_handoff_lines"' "$CONFIG_FILE" 2>/dev/null | sed 's/[^0-9]//g' | head -1)
  [ -n "$_hf" ] && FALLBACK_HANDOFF_LINES="$_hf"
fi
STALE_SECONDS=$(( STALE_HOURS * 3600 ))

# kernel 상태 판정: fresh / stale / missing
KERNEL_STATE="missing"
if [ -f "$KERNEL_FILE" ]; then
  KERNEL_MTIME=$(file_mtime "$KERNEL_FILE")
  NOW=$(date +%s)
  AGE=$(( NOW - KERNEL_MTIME ))
  AGE_H=$(( AGE / 3600 ))
  if [ "$AGE" -gt "$STALE_SECONDS" ]; then
    KERNEL_STATE="stale"
  else
    KERNEL_STATE="fresh"
  fi
fi

# kernel fresh → 기존 로직 (kernel 내용 출력)
if [ "$KERNEL_STATE" = "fresh" ]; then
  echo "=== [session_start: $SOURCE] 이전 세션 상태 ==="

  # TASKS 상단 (원본 문서 우선)
  echo "--- TASKS 상단 ---"
  head -"$FALLBACK_TASKS_LINES" "$PATH_TASKS" 2>/dev/null
  # HANDOFF 최신 세션
  echo "--- HANDOFF 최신 세션 ---"
  head -"$FALLBACK_HANDOFF_LINES" "$PATH_HANDOFF" 2>/dev/null

  # progress.json 캐시 (참고용, 원본 문서 뒤에 출력)
  PROGRESS_FILE="$PROJECT_ROOT/.claude/state/session_progress.json"
  if [ -f "$PROGRESS_FILE" ]; then
    CURRENT_TASK=$(grep '"current_task"' "$PROGRESS_FILE" 2>/dev/null | sed 's/.*: *"\(.*\)".*/\1/' | head -1)
    if [ -n "$CURRENT_TASK" ] && [ "$CURRENT_TASK" != "" ]; then
      echo "--- 이전 작업 (캐시, 참고용) ---"
      echo "진행 중: $CURRENT_TASK"
    fi
  fi

  echo "=== session_kernel 끝 ==="
  hook_log "session_start_restore" "kernel fresh — 출력 완료 source=$SOURCE age=${AGE}s"

# kernel stale/missing → fallback: TASKS + HANDOFF 직접 읽기 (Phase 2 개선)
else
  if [ "$KERNEL_STATE" = "stale" ]; then
    echo "[session_start] ⚠️ session_kernel.md가 ${AGE_H}시간 전 저장 — stale. 원본 문서 fallback 사용."
  else
    echo "[session_start] session_kernel.md 없음 — 원본 문서 fallback 사용."
  fi

  echo "=== [session_start: $SOURCE] fallback — 원본 문서 직접 읽기 ==="

  # TASKS 상단 (복구 우선순위 1위)
  echo "--- TASKS 상단 (${FALLBACK_TASKS_LINES}줄) ---"
  head -"$FALLBACK_TASKS_LINES" "$PATH_TASKS" 2>/dev/null || echo "(TASKS.md 없음)"

  # HANDOFF 최신 세션 (복구 우선순위 2위)
  echo "--- HANDOFF 최신 세션 (${FALLBACK_HANDOFF_LINES}줄) ---"
  head -"$FALLBACK_HANDOFF_LINES" "$PATH_HANDOFF" 2>/dev/null || echo "(HANDOFF.md 없음)"

  # 활성 도메인 (있으면 1줄)
  DOMAIN_REQ="$PROJECT_ROOT/.claude/state/active_domain.req"
  if [ -f "$DOMAIN_REQ" ]; then
    echo "--- 활성 도메인: $(cat "$DOMAIN_REQ") ---"
  fi

  # progress.json 캐시 (참고용, 맨 뒤)
  PROGRESS_FILE="$PROJECT_ROOT/.claude/state/session_progress.json"
  if [ -f "$PROGRESS_FILE" ]; then
    CURRENT_TASK=$(grep '"current_task"' "$PROGRESS_FILE" 2>/dev/null | sed 's/.*: *"\(.*\)".*/\1/' | head -1)
    if [ -n "$CURRENT_TASK" ] && [ "$CURRENT_TASK" != "" ]; then
      echo "--- 이전 작업 (캐시, 참고용) ---"
      echo "진행 중: $CURRENT_TASK"
    fi
  fi

  echo "=== fallback 끝 ==="
  hook_log "session_start_restore" "kernel $KERNEL_STATE — fallback 출력 source=$SOURCE"
fi

hook_log "session_start_restore" "kernel 출력 완료 source=$SOURCE age=${AGE}s"

# Fast smoke subset — 로컬·결정적 검증만 (차단 아님, 경고만)
FAST_SMOKE="$(dirname "$0")/smoke_fast.sh"
if [ -x "$FAST_SMOKE" ]; then
  FAST_RESULT=$("$FAST_SMOKE" 2>&1)
  echo "$FAST_RESULT"
  hook_log "session_start_restore" "fast_smoke: $FAST_RESULT"
fi

exit 0
