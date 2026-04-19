#!/bin/bash
# PreToolUse hook — HARNESS GATE: 토론모드 GPT 응답 후 하네스 분석 없이 행동 차단
#
# 발화 조건: debate_preflight.req 존재 시에만 활성
# 차단 경로: Bash(git commit/push/share-result/finish). GPT 전송은 Chrome MCP로 통일(2026-04-13)
# 검사 대상: 트랜스크립트에서 하네스 분석 복합 조건 충족 여부
#
# 복합 조건 (GPT 합의 2라운드):
#   1. "채택:" 존재
#   2. "보류:" 또는 "버림:" 존재
#   3. 독립 견해 마커 (반론|대안|내 판단|환경상|독립 대조|이견)
#   4. 실물근거 마커 (실증됨|Git|커밋|diff|실물|기준 미확인)
#
# 4개 AND 조건 전부 충족 시에만 통과

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/hook_common.sh" 2>/dev/null || true
# 훅 등급: gate (Phase 2-C 2026-04-19 세션73 timing 배선, exit 2 승격은 1주 수집 후)
_HG_START=$(hook_timing_start)

# --- debate_preflight.req 존재 확인 ---
SESSION_KEY="$(session_key)"
SESSION_DIR="$STATE_EVIDENCE/$SESSION_KEY"
REQ_DIR="$SESSION_DIR/requires"
REQ_FILE="$REQ_DIR/debate_preflight.req"

if [ ! -f "$REQ_FILE" ]; then
  # 토론 도메인이 아니면 무조건 통과
  hook_timing_end "harness_gate" "$_HG_START" "skip_nondebate"
  exit 0
fi

# --- 대상 도구 필터 ---
TOOL_NAME=""
if type safe_json_get >/dev/null 2>&1; then
  TOOL_NAME=$(printf '%s' "$INPUT" | safe_json_get "tool_name" 2>/dev/null || true)
fi
if [ -z "$TOOL_NAME" ]; then
  TOOL_NAME=$(echo "$INPUT" | sed -n 's/.*"tool_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
fi

# Bash 도구만 검사 (commit/push/share 경로)
if [[ "$TOOL_NAME" != *"Bash"* ]]; then
  hook_timing_end "harness_gate" "$_HG_START" "skip_nonbash"
  exit 0
fi

# --- Bash 명령어 필터: commit/push/공유 경로만 차단 ---
TOOL_INPUT=""
if type safe_json_get >/dev/null 2>&1; then
  TOOL_INPUT=$(printf '%s' "$INPUT" | safe_json_get "tool_input" 2>/dev/null || true)
fi
if [ -z "$TOOL_INPUT" ]; then
  TOOL_INPUT="$INPUT"
fi

# git commit, git push, share-result, finish 중 하나가 포함된 경우만 검사
IS_ACTION="NO"
if echo "$TOOL_INPUT" | grep -qiE '(git commit|git push|share.result|finish)'; then
  IS_ACTION="YES"
fi

if [[ "$IS_ACTION" != "YES" ]]; then
  hook_timing_end "harness_gate" "$_HG_START" "skip_nonaction"
  exit 0
fi

# --- 트랜스크립트에서 하네스 분석 복합 조건 검사 ---
TRANSCRIPT_PATH=""
if type safe_json_get >/dev/null 2>&1; then
  TRANSCRIPT_PATH=$(printf '%s' "$INPUT" | safe_json_get "transcript_path" 2>/dev/null || true)
fi

# 트랜스크립트 경로가 없으면: debate_preflight 활성 시 차단 (fail-closed)
# GPT 합의 3라운드: transcript_path 미확인 + debate_preflight.req 존재 → 우회 구멍 방지
if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
  hook_log "PreToolUse/harness_gate" "BLOCK: transcript_path 미확인 + debate_preflight 활성 → fail-closed" 2>/dev/null
  echo '{"hookSpecificOutput":{"permissionDecision":"deny","permissionDecisionReason":"[하네스 게이트] 토론 모드 활성 상태에서 트랜스크립트를 읽을 수 없습니다. 하네스 분석(채택/보류/버림 + 독립 견해 + 실물 근거)을 수행한 후 다시 시도하세요."}}'
  hook_timing_end "harness_gate" "$_HG_START" "block_notranscript"
  exit 0
fi

# 최근 assistant 발화 추출 (마지막 5000자)
RECENT=$(tail -c 20000 "$TRANSCRIPT_PATH" 2>/dev/null || true)

# 복합 조건 검사
HAS_ADOPT="NO"
HAS_HOLD_OR_DISCARD="NO"
HAS_INDEPENDENT="NO"
HAS_EVIDENCE="NO"

if echo "$RECENT" | grep -qE '채택:'; then
  HAS_ADOPT="YES"
fi

if echo "$RECENT" | grep -qE '(보류:|버림:)'; then
  HAS_HOLD_OR_DISCARD="YES"
fi

if echo "$RECENT" | grep -qE '(반론|대안|내 판단|환경상|독립 대조|독립 의견|독립 견해|이견|내 입장)'; then
  HAS_INDEPENDENT="YES"
fi

if echo "$RECENT" | grep -qE '(실증됨|Git|커밋|diff|실물|기준 미확인|일반론)'; then
  HAS_EVIDENCE="YES"
fi

if [[ "$HAS_ADOPT" == "YES" && "$HAS_HOLD_OR_DISCARD" == "YES" && "$HAS_INDEPENDENT" == "YES" && "$HAS_EVIDENCE" == "YES" ]]; then
  hook_log "PreToolUse/harness_gate" "PASS: 하네스 분석 복합 조건 충족 (adopt=$HAS_ADOPT hold/discard=$HAS_HOLD_OR_DISCARD independent=$HAS_INDEPENDENT evidence=$HAS_EVIDENCE)" 2>/dev/null
  hook_timing_end "harness_gate" "$_HG_START" "pass"
  exit 0
fi

# --- 차단 ---
MISSING=""
[[ "$HAS_ADOPT" != "YES" ]] && MISSING="${MISSING} 채택:"
[[ "$HAS_HOLD_OR_DISCARD" != "YES" ]] && MISSING="${MISSING} 보류:/버림:"
[[ "$HAS_INDEPENDENT" != "YES" ]] && MISSING="${MISSING} 독립견해"
[[ "$HAS_EVIDENCE" != "YES" ]] && MISSING="${MISSING} 실물근거"

hook_log "PreToolUse/harness_gate" "BLOCK: 하네스 미수행 → 누락:${MISSING}" 2>/dev/null
hook_incident "hook_block" "harness_gate" "" "하네스 분석 미수행. 누락:${MISSING}" '"classification_reason":"harness_missing"' 2>/dev/null || true

echo "{\"hookSpecificOutput\":{\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"[하네스 게이트] GPT 응답에 대한 하네스 분석이 부족합니다. 누락 항목:${MISSING}. 채택:/보류:/버림: + 독립 견해 + 실물 근거를 포함한 하네스 분석을 수행한 후 다시 시도하세요.\"}}"
hook_timing_end "harness_gate" "$_HG_START" "block_incomplete"
exit 0
