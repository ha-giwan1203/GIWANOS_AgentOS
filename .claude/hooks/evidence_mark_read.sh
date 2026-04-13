#!/bin/bash
# PostToolUse(Read|Grep|Glob|Bash|Write|Edit|MultiEdit)
# 읽기/검증/문서갱신 증거 마커 적립

source "$(dirname "$0")/hook_common.sh" 2>/dev/null

INPUT="$(cat)"

SESSION_KEY="$(session_key)"
SESSION_DIR="$STATE_EVIDENCE/$SESSION_KEY"
PROOF_DIR="$SESSION_DIR/proofs"
START_FILE="$SESSION_DIR/.session_start"

mkdir -p "$PROOF_DIR"

if [ ! -f "$START_FILE" ]; then
  : > "$START_FILE"
fi

mark() {
  local name="$1"
  : > "$PROOF_DIR/$name.ok"
  hook_log "PostToolUse/evidence_mark_read" "mark=$name"
}

TEXT="$(printf '%s' "$INPUT" | tr '\n' ' ' | sed 's/\\"/"/g')"

# Windows 경로 정규화: 백슬래시 → 슬래시 (경로별 정밀 매칭용)
NORM_TEXT="$(echo "$TEXT" | sed 's/\\\\/\//g')"

# 도메인/기준 문서 읽기
echo "$NORM_TEXT" | grep -qE 'SKILL\.md' && mark "skill_read"
echo "$NORM_TEXT" | grep -qE '(^|/|\\)CLAUDE\.md' && mark "domain_read"
echo "$NORM_TEXT" | grep -qE 'TASKS\.md' && mark "tasks_read"
echo "$NORM_TEXT" | grep -qE 'HANDOFF\.md' && mark "handoff_read"
echo "$NORM_TEXT" | grep -qE 'STATUS\.md' && mark "status_read"

# 토론모드 전용 마커 (경로 정밀 매칭) — 레거시 호환 유지
INSTRUCTION_DIR="$PROJECT_ROOT/.claude/state/instruction_reads"
mkdir -p "$INSTRUCTION_DIR"

if echo "$NORM_TEXT" | grep -qE '토론모드/ENTRY\.md'; then
  : > "$INSTRUCTION_DIR/debate_entry_read.ok"
  hook_log "PostToolUse/evidence_mark_read" "instruction_mark=debate_entry_read"
fi

if echo "$NORM_TEXT" | grep -qE '토론모드/CLAUDE\.md'; then
  : > "$INSTRUCTION_DIR/debate_claude_read.ok"
  hook_log "PostToolUse/evidence_mark_read" "instruction_mark=debate_claude_read"
fi

# 도메인 진입 동적 마커 (JSON registry 기반)
# GPT 합의(세션33): required_docs[{id, path}] 기반 domain_<domain_id>__<doc_id>.ok 자동 생성
DOMAIN_REGISTRY="$PROJECT_ROOT/.claude/domain_entry_registry.json"
DOMAIN_REQ="$PROJECT_ROOT/.claude/state/active_domain.req"
if [ -f "$DOMAIN_REGISTRY" ] && [ -f "$DOMAIN_REQ" ]; then
  ACTIVE_DOMAIN=$(grep '^domain_id=' "$DOMAIN_REQ" | cut -d= -f2)
  if [ -n "$ACTIVE_DOMAIN" ]; then
    # JSON에서 해당 도메인의 required_docs path 목록 추출
    IN_DOMAIN=0
    IN_DOCS=0
    while IFS= read -r line; do
      if echo "$line" | grep -q "\"$ACTIVE_DOMAIN\""; then
        IN_DOMAIN=1
      fi
      if [ "$IN_DOMAIN" -eq 1 ] && echo "$line" | grep -q '"required_docs"'; then
        IN_DOCS=1
      fi
      if [ "$IN_DOMAIN" -eq 1 ] && [ "$IN_DOCS" -eq 1 ]; then
        DOC_ID=$(echo "$line" | grep '"id"' | sed 's/.*: *"//;s/".*//')
        DOC_PATH=$(echo "$line" | grep '"path"' | sed 's/.*: *"//;s/".*//')
        if [ -n "$DOC_ID" ] && [ -n "$DOC_PATH" ]; then
          # 읽기 텍스트에 해당 경로가 포함되면 마커 생성
          ESCAPED_PATH=$(echo "$DOC_PATH" | sed 's/\//\\\//g')
          if echo "$NORM_TEXT" | grep -qF "$DOC_PATH"; then
            MARKER_NAME="domain_${ACTIVE_DOMAIN}__${DOC_ID}"
            : > "$INSTRUCTION_DIR/${MARKER_NAME}.ok"
            hook_log "PostToolUse/evidence_mark_read" "domain_instruction_mark=$MARKER_NAME"
          fi
        fi
      fi
      if [ "$IN_DOMAIN" -eq 1 ] && [ "$IN_DOCS" -eq 1 ] && echo "$line" | grep -q '^\s*\]'; then
        IN_DOCS=0
        IN_DOMAIN=0
      fi
    done < "$DOMAIN_REGISTRY"
  fi
fi

# 전용 진단 스크립트 성공 흔적
echo "$TEXT" | grep -qE 'date_check(\.sh)?' && mark "date_check"
echo "$TEXT" | grep -qE 'auth_diag(\.sh)?' && mark "auth_diag"
echo "$TEXT" | grep -qE 'identifier_ref_check(\.sh)?|기준정보 대조|identifier_ref' && mark "identifier_ref"

# 문서 갱신 흔적
echo "$TEXT" | grep -qE 'TASKS\.md' && echo "$TEXT" | grep -qE '(Write|Edit|MultiEdit|file_path|path)' && mark "tasks_updated"
echo "$TEXT" | grep -qE 'HANDOFF\.md' && echo "$TEXT" | grep -qE '(Write|Edit|MultiEdit|file_path|path)' && mark "handoff_updated"

exit 0
