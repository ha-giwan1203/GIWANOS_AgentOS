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

# progress.json writer: compact 직전 현재 상태를 JSON으로 갱신 (원자적 저장)
# TASKS.md "다음 세션 안건" 행에서 current_task 추출
CURRENT_TASK=$(grep -A 1 "^## 다음 세션 안건" "$PATH_TASKS" 2>/dev/null | tail -1 | sed 's/^[[:space:]]*//')
[ "$CURRENT_TASK" = "(없음)" ] && CURRENT_TASK=""
SAVE_TS=$(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || echo "")
SESSION_ID="${CLAUDE_TRANSCRIPT_PATH:-unknown}"

PROGRESS_TMP="${PROGRESS_FILE}.tmp"
cat > "$PROGRESS_TMP" << PJSON
{
  "_comment": "캐시 전용 — 상태 원본이 아님. 복구 우선순위: TASKS.md > STATUS.md > HANDOFF.md > 이 파일",
  "schema_version": 1,
  "saved_at": "$SAVE_TS",
  "session_id": "$SESSION_ID",
  "active_domain": "${ACTIVE_DOMAIN:-}",
  "current_task": "$CURRENT_TASK",
  "completed_this_session": [],
  "next_actions": [],
  "blockers": []
}
PJSON
if [ -s "$PROGRESS_TMP" ]; then
  mv "$PROGRESS_TMP" "$PROGRESS_FILE"
fi

# task_cursor.json 파생 캐시 (Phase 3-3: TASKS.md 파싱 강화)
# TASKS.md에서만 읽어 생성. 수동 편집 금지. 원본은 항상 TASKS.md.
CURSOR_FILE="$STATE_DIR/task_cursor.json"
CURSOR_TMP="${CURSOR_FILE}.tmp"
# next_step: "다음 세션 안건" 아래 첫 비빈 줄
NEXT_STEP=$(grep -A 2 "^## 다음 세션 안건" "$PATH_TASKS" 2>/dev/null | grep -v "^##" | grep -v "^--" | head -1 | sed 's/^[[:space:]]*//')
# last_completed: 가장 최근 [완료] 항목 제목
LAST_COMPLETED=$(grep -A 1 "^### \[완료\]" "$PATH_TASKS" 2>/dev/null | head -1 | sed 's/^### \[완료\] //' | sed 's/ — .*//')
# current_phase: TASKS.md "최종 업데이트" 행에서 괄호 안 Phase 추출
CURRENT_PHASE=$(grep "^최종 업데이트:" "$PATH_TASKS" 2>/dev/null | sed 's/.*(\(.*\)).*/\1/' | head -1)
# last_verified_sha: HANDOFF.md에서 GPT 통과/정합 판정이 있는 마지막 커밋 SHA (없으면 빈값)
LAST_VERIFIED_SHA=$(grep -oE '[0-9a-f]{7,8}' "$PATH_HANDOFF" 2>/dev/null | tail -1)
[ -z "$LAST_VERIFIED_SHA" ] && LAST_VERIFIED_SHA=""
cat > "$CURSOR_TMP" << TCJSON
{
  "_comment": "파생 캐시 — TASKS.md/HANDOFF.md에서만 생성. 수동 편집 금지.",
  "saved_at": "$SAVE_TS",
  "current_phase": "$CURRENT_PHASE",
  "next_step": "$NEXT_STEP",
  "last_completed": "$LAST_COMPLETED",
  "last_verified_sha": "$LAST_VERIFIED_SHA",
  "blocked": false
}
TCJSON
if [ -s "$CURSOR_TMP" ]; then
  mv "$CURSOR_TMP" "$CURSOR_FILE"
fi

# progress.json 스냅샷 (있으면 kernel에 포함)
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
