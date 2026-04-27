#!/bin/bash
# PostToolUse(Read|Grep|Glob|Bash|Write|Edit|MultiEdit)
# 읽기/검증/문서갱신 증거 마커 적립

source "$(dirname "$0")/hook_common.sh" 2>/dev/null
# 훅 등급: measurement (Phase 2-C 2026-04-19 세션73 timing 배선)
_EMR_START=$(hook_timing_start)

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

# 세션93 (2026-04-22 2자 토론 합의, plan.md 1주차 4번 (d)):
#   C분류 "직접 의존 못 찾은 마커" 5종 삭제:
#     skill_read.ok (단일) / domain_read / tasks_read / handoff_read / status_read
#   유지: skill_read__<SKILL_ID>.ok (skill_instruction_gate 전담 — B분류 instruction/control 축)
# 스킬별 SKILL.md 개별 마커 (skill_instruction_gate.sh 연동, B분류 유지)
SKILL_ID=$(echo "$NORM_TEXT" | sed -n 's|.*[/\\]스킬[/\\]\([^/\\]*\)[/\\]SKILL\.md.*|\1|p' | head -1)
if [ -n "$SKILL_ID" ]; then
  mark "skill_read__${SKILL_ID}"
fi

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

# 세션113 (3자 토론 만장일치, 2026-04-27, debate_20260427_105243_3way)
# Option B 채택 — evidence_mark_read.sh 패턴 확장으로 정상 OAuth 작업 ok 인정
# 양측(GPT/Gemini) 합의 안전 조건 (false ok 방지):
#   1. 단순 스크립트명 매칭 금지 — 명령 + 명시적 성공 신호 + error 부재 3중 조건
#   2. grep -qF fixed-string 매칭으로 정규식 메타문자 우회 차단 (Gemini 앵커링 강제)
#   3. error/traceback/exception/failed 키워드 부재 추가 검증
#   4. token 파일 mtime이 세션 시작 이후인지 검증 (GPT 추가 보강: "이번 실행에서 갱신된 파일")
#   5. 단일 파일 최소 보정 — 신규 hook 금지, settings 변경 금지, evidence_gate 정책 변경 금지
# 본 수정이 마지막 시스템 개입 (세션108 합의 일관성 유지). 향후 P2-C/P3-E 재논의는 트리거 충족 시만.

# 패턴 1: erp_oauth_login.py 명령 + OAuth 성공 신호 + error 부재 (stdout 성공 텍스트 기반)
if echo "$TEXT" | grep -qF 'erp_oauth_login.py' && \
   echo "$TEXT" | grep -qF 'OAuth' && \
   ! echo "$TEXT" | grep -qiE '(error|traceback|exception|failed)'; then
  mark "auth_diag"
  hook_log "PostToolUse/evidence_mark_read" "auth_diag_marked_via_oauth_normal_flow"
fi

# 패턴 2: ERP OAuth 토큰 파일이 세션 시작 이후 생성/갱신된 경우 (산출물 mtime 기반)
SESSION_START_EPOCH=$(stat -c %Y "$START_FILE" 2>/dev/null || echo 0)
ERP_TOKEN_FILE="$PROJECT_ROOT/.claude/state/erp_oauth_token.json"
if [ -f "$ERP_TOKEN_FILE" ] && [ "$SESSION_START_EPOCH" -gt 0 ]; then
  TOKEN_MTIME=$(stat -c %Y "$ERP_TOKEN_FILE" 2>/dev/null || echo 0)
  if [ "$TOKEN_MTIME" -ge "$SESSION_START_EPOCH" ]; then
    mark "auth_diag"
    hook_log "PostToolUse/evidence_mark_read" "auth_diag_marked_via_token_mtime"
  fi
fi

# 세션93 (2026-04-22 2자 토론 합의, plan.md 1주차 4번 (d)):
#   tasks_updated / handoff_updated 마커 생성 제거.
#   사유: evidence_gate에서 tasks_handoff 블록 제거됨 → 이 마커는 더 이상 참조되지 않음.
#   commit 시점 TASKS/HANDOFF 갱신 검증은 commit_gate(final_check)와 completion_gate(write_marker)가 담당.

hook_timing_end "evidence_mark_read" "$_EMR_START" "ok"
exit 0
