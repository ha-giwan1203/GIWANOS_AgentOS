#!/bin/bash
# PreCompact hook: compact 직전 session_kernel.md에 현재 상태 저장
# auto-compact / manual compact 모두 트리거됨 (v1.0.48+)
# v2: 활성 도메인 규칙 + progress.json 스냅샷 추가 (하네스 강화 Phase 1)

source "$(dirname "$0")/hook_common.sh"

TIMESTAMP=$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M KST' 2>/dev/null || date '+%Y-%m-%d %H:%M')
STATE_DIR="$PROJECT_ROOT/.claude/state"
KERNEL_FILE="$STATE_DIR/session_kernel.md"
DOMAIN_REQ="$STATE_DIR/active_domain.req"
DOMAIN_REGISTRY="$PROJECT_ROOT/.claude/domain_entry_registry.json"
PROGRESS_FILE="$STATE_DIR/session_progress.json"

mkdir -p "$STATE_DIR"

# TASKS.md 상단 35줄 (현재 의제)
TASKS_EXCERPT=$(head -35 "$PATH_TASKS" 2>/dev/null || echo "(TASKS.md 없음)")

# HANDOFF.md 상단 50줄 (최신 세션이 상단에 위치)
HANDOFF_EXCERPT=$(head -50 "$PATH_HANDOFF" 2>/dev/null || echo "(HANDOFF.md 없음)")

# 활성 도메인 + 필수 문서 경로 수집
DOMAIN_SECTION=""
if [ -f "$DOMAIN_REQ" ]; then
  ACTIVE_DOMAIN=$(cat "$DOMAIN_REQ" 2>/dev/null)
  if [ -n "$ACTIVE_DOMAIN" ] && [ -f "$DOMAIN_REGISTRY" ]; then
    # 도메인 필수 문서 경로 추출
    REQUIRED_DOCS=$(grep -A 20 "\"domain_id\".*\"$ACTIVE_DOMAIN\"" "$DOMAIN_REGISTRY" 2>/dev/null \
      | grep '"path"' | sed 's/.*"path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' | head -5)
    DOMAIN_SECTION="## 활성 도메인: $ACTIVE_DOMAIN
필수 문서:
$REQUIRED_DOCS"
  fi
fi

# progress.json 스냅샷 (있으면 포함)
PROGRESS_SECTION=""
if [ -f "$PROGRESS_FILE" ]; then
  PROGRESS_SECTION="## 작업 진행 상태 (session_progress.json)
$(cat "$PROGRESS_FILE" 2>/dev/null)"
fi

# 원자적 저장: tmp → 검증 → rename (GPT 채택: 중간 종료 시 깨진 파일 방지)
KERNEL_TMP="${KERNEL_FILE}.tmp"
cat > "$KERNEL_TMP" << KERNEL
# Session Kernel (PreCompact 저장: $TIMESTAMP)
> compact 후 세션 재개 시 자동 로드. 직접 편집 금지 — precompact_save.sh가 덮어씀.

$DOMAIN_SECTION

$PROGRESS_SECTION

## TASKS 현재 의제 (상단 35줄)
$TASKS_EXCERPT

## HANDOFF 현재 상태 (상단 50줄)
$HANDOFF_EXCERPT
KERNEL

# tmp 검증 후 rename
if [ -s "$KERNEL_TMP" ]; then
  mv "$KERNEL_TMP" "$KERNEL_FILE"
else
  rm -f "$KERNEL_TMP"
  hook_log "precompact_save" "WARN: kernel tmp 비어있음 — 저장 스킵"
  exit 0
fi

hook_log "precompact_save" "session_kernel 저장 완료: $TIMESTAMP domain=${ACTIVE_DOMAIN:-none}"
echo "[precompact_save] session_kernel.md 저장 완료 ($TIMESTAMP)" >&2
exit 0
