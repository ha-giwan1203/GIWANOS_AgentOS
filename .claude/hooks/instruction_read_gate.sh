#!/bin/bash
# PreToolUse(Bash) — GPT 전송 직전 지침 읽기 강제 게이트
# share-result / finish 실행 전
# ENTRY.md + 토론모드 CLAUDE.md 읽기 여부 확인
# 미읽기 시 deny+exit 2

source "$(dirname "$0")/hook_common.sh" 2>/dev/null

INPUT="$(cat)"
COMMAND="$(echo "$INPUT" | safe_json_get "command" 2>/dev/null)"

# GPT 전송 관련 명령만 검사
is_gpt_send() {
  # /finish 스킬만 매칭, finish_state.json 등 오탐 방지
  echo "$COMMAND" | grep -qE 'share-result|/finish([^_a-zA-Z0-9]|$)'
}

if ! is_gpt_send; then
  exit 0
fi

INSTRUCTION_DIR="$PROJECT_ROOT/.claude/state/instruction_reads"
DOMAIN_REQ="$PROJECT_ROOT/.claude/state/active_domain.req"
DOMAIN_REGISTRY="$PROJECT_ROOT/.claude/domain_entry_registry.json"

# 활성 도메인 기반 동적 마커 검사 (2차 하네스 — GPT 합의 세션33)
MISSING=""
if [ -f "$DOMAIN_REQ" ] && [ -f "$DOMAIN_REGISTRY" ]; then
  ACTIVE_DOMAIN=$(grep '^domain_id=' "$DOMAIN_REQ" | cut -d= -f2)
  if [ -n "$ACTIVE_DOMAIN" ]; then
    # JSON에서 해당 도메인의 required_docs 추출
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
          MARKER="$INSTRUCTION_DIR/domain_${ACTIVE_DOMAIN}__${DOC_ID}.ok"
          if [ ! -f "$MARKER" ]; then
            MISSING="$MISSING\n  - $DOC_PATH"
          fi
        fi
      fi
      if [ "$IN_DOMAIN" -eq 1 ] && [ "$IN_DOCS" -eq 1 ] && echo "$line" | grep -q '^\s*\]'; then
        IN_DOCS=0
        IN_DOMAIN=0
      fi
    done < "$DOMAIN_REGISTRY"
  fi
else
  # 레거시 fallback: active_domain.req 없으면 토론모드 하드코딩 검사 유지
  ENTRY_OK="$INSTRUCTION_DIR/debate_entry_read.ok"
  CLAUDE_OK="$INSTRUCTION_DIR/debate_claude_read.ok"
  if [ ! -f "$ENTRY_OK" ]; then
    MISSING="$MISSING\n  - 90_공통기준/토론모드/ENTRY.md"
  fi
  if [ ! -f "$CLAUDE_OK" ]; then
    MISSING="$MISSING\n  - 90_공통기준/토론모드/CLAUDE.md"
  fi
fi

if [ -n "$MISSING" ]; then
  MISSING_ESCAPED=$(printf '%s' "$MISSING" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\n/\\n/g')
  MSG="[instruction_read_gate] GPT 전송 차단: 필수 지시문 미읽기.${MISSING_ESCAPED}\\n\\n먼저 위 파일을 Read/Grep으로 읽은 후 다시 시도하세요."
  hook_log "instruction_read_gate" "DENY missing=$(echo "$MISSING" | tr '\n' ',')"
  hook_incident "instruction_read_gate" "instruction_not_read" "GPT 전송 전 필수 지시문 미읽기: $MISSING"
  printf '{"hookSpecificOutput":{"permissionDecision":"deny"},"systemMessage":"%s"}' "$MSG" >&2
  exit 2
fi

hook_log "instruction_read_gate" "PASS domain=${ACTIVE_DOMAIN:-legacy} docs confirmed"
exit 0
