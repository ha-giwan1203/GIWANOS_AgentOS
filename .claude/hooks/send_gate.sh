#!/bin/bash
# PreToolUse hook — SEND GATE: ChatGPT 직접 javascript_tool 예비 전송 전 미확인 응답 점검 강제
# 대상: mcp__Claude_in_Chrome__javascript_tool 호출 중 execCommand('insertText') 포함 시
# 참고: cdp_chat_send.py 기본 경로는 최신 답변 기대값 비교 + mark-send-gate를 자체 처리하며, 이 hook은 직접 JS 예비 경로 보호용이다.
# 조건: .claude/state/send_gate_passed 파일이 120초 이내에 갱신되어 있어야 통과
# GPT 합의: 2026-04-06 — 문서 규칙만으로 부족, 실행 강제 gate 필요

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/hook_common.sh" 2>/dev/null || true

json_value() {
  local payload="$1"
  local key="$2"
  if type safe_json_get >/dev/null 2>&1; then
    printf '%s' "$payload" | safe_json_get "$key" 2>/dev/null || true
  fi
}

# hook_common safe_json_get 우선, 실패 시 기존 추출 fallback
TOOL_NAME=$(json_value "$INPUT" "tool_name")
if [ -z "$TOOL_NAME" ]; then
  TOOL_NAME=$(echo "$INPUT" | sed -n 's/.*"tool_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
fi

# javascript_tool 예비 경로가 아니면 통과 (기본 경로 cdp_chat_send.py는 자체 검증)
if [[ "$TOOL_NAME" != *"javascript_tool"* ]]; then
  exit 0
fi

# 가능하면 실제 tool_input/code 범위만 검사하고, 실패 시 원문 전체 fallback
TOOL_INPUT=$(json_value "$INPUT" "tool_input")
TOOL_CODE=$(json_value "$TOOL_INPUT" "code")
TOOL_TEXT=$(json_value "$TOOL_INPUT" "text")

INSPECT_SOURCE="$INPUT"
if [ -n "$TOOL_INPUT" ]; then
  INSPECT_SOURCE="$TOOL_INPUT"
fi
if [ -n "$TOOL_CODE" ]; then
  INSPECT_SOURCE="$TOOL_CODE"
fi

QUALITY_SOURCE="$INSPECT_SOURCE"
if [ -n "$TOOL_TEXT" ]; then
  QUALITY_SOURCE="$TOOL_TEXT"
fi

# text 파라미터에 execCommand + insertText 패턴 확인
HAS_INSERT="NO"
if echo "$INSPECT_SOURCE" | grep -q 'execCommand' && echo "$INSPECT_SOURCE" | grep -q 'insertText'; then
  HAS_INSERT="YES"
fi

# insertText가 아니면 통과 (일반 JS 실행은 차단하지 않음)
if [[ "$HAS_INSERT" != "YES" ]]; then
  exit 0
fi

# debate 도메인 활성 확인 — 토론모드가 아니면 통과
DEBATE_FLAG="${TEMP:-/tmp}/.claude_domain_debate_active"
if [ -f "$DEBATE_FLAG" ]; then
  ACTIVE_DOMAIN=$(cat "$DEBATE_FLAG" 2>/dev/null)
  if [[ "$ACTIVE_DOMAIN" != "debate" ]]; then
    exit 0
  fi
else
  exit 0
fi

# SEND GATE 파일 확인
STATE_DIR="$SCRIPT_DIR/../state"
mkdir -p "$STATE_DIR" 2>/dev/null
GATE_FILE="$STATE_DIR/send_gate_passed"

if [ ! -f "$GATE_FILE" ]; then
  echo '{"decision":"block","reason":"SEND GATE 미통과: 전송 전 미확인 응답 점검(assistant 최신 텍스트 재읽기)을 먼저 실행하세요. 점검 후 .claude/state/send_gate_passed 파일을 갱신해야 전송이 허용됩니다."}'
  exit 0
fi

# 120초 이내 갱신 확인 (bash-only, python3 의존 제거)
GATE_MTIME=$(stat --format=%Y "$GATE_FILE" 2>/dev/null || stat -f %m "$GATE_FILE" 2>/dev/null || echo 0)
NOW_EPOCH=$(date +%s 2>/dev/null || echo 9999)
GATE_AGE=$((NOW_EPOCH - GATE_MTIME))

if [[ "$GATE_AGE" -gt 120 ]]; then
  echo '{"decision":"block","reason":"SEND GATE 만료('"$GATE_AGE"'초 경과): 전송 전 미확인 응답 점검을 다시 실행하세요. 120초 이내 점검만 유효합니다."}'
  exit 0
fi

# === 독립 검증 게이트 ===
# 하네스 라벨(채택/보류/버림)이 포함된 반박문이면 independent_review.md 존재 필수
# GPT 합의 2026-04-10: 의지 기반 규칙 실패 → 코드 강제로 순서 보장
HARNESS_LABELS='(채택:|보류:|버림:)'
if echo "$QUALITY_SOURCE" | grep -qE "$HARNESS_LABELS"; then
  REVIEW_FILE="$STATE_DIR/independent_review.md"
  if [ ! -f "$REVIEW_FILE" ]; then
    hook_log "PreToolUse/send_gate" "BLOCK: independent_review missing" 2>/dev/null
    echo '{"decision":"block","reason":"[독립 검증 게이트] 하네스 분석 결과(채택/보류/버림)가 포함된 반박문입니다. 독립 검증(.claude/state/independent_review.md)을 먼저 수행하세요. GPT 응답을 읽기 전에 관련 파일을 독립적으로 리뷰하고, 내 문제 목록을 만든 뒤 GPT 주장과 대조해야 합니다."}'
    exit 0
  fi
  # 현재 세션에서 생성된 파일인지 확인 (300초 이내)
  REVIEW_MTIME=$(stat --format=%Y "$REVIEW_FILE" 2>/dev/null || stat -f %m "$REVIEW_FILE" 2>/dev/null || echo 0)
  REVIEW_AGE=$((NOW_EPOCH - REVIEW_MTIME))
  if [[ "$REVIEW_AGE" -gt 3600 ]]; then
    hook_log "PreToolUse/send_gate" "BLOCK: independent_review stale (${REVIEW_AGE}s)" 2>/dev/null
    echo '{"decision":"block","reason":"[독립 검증 게이트] independent_review.md가 '"$REVIEW_AGE"'초 전 파일입니다. 현재 세션에서 새로 독립 검증을 수행하세요."}'
    exit 0
  fi
fi

# === 토론 품질 경량 검사 (debate_quality_gate-lite) ===
# debate 도메인 활성 상태에서만 동작 — 반론/대안 0건 금지
# GPT 합의 2026-04-07: send_gate 내부 경량 검사로 역할 오염 최소화
OPINION_MARKERS='(반론|대안|다른 접근|내 판단|Claude 판단|환경상 비적합|내 독립 견해|내 우려)'
if echo "$QUALITY_SOURCE" | grep -qE "$OPINION_MARKERS"; then
  # 독립 견해 마커 존재 → 통과
  :
else
  # 단순 보고/SHA 공유는 허용 (커밋/푸시/SHA/diff/PASS/검증 키워드)
  if echo "$QUALITY_SOURCE" | grep -qE '(커밋|푸시|SHA|diff|PASS|FAIL|검증 결과|판정 요청|수정 완료)'; then
    :  # 보고성 메시지 → 검사 건너뜀
  else
    hook_log "PreToolUse/send_gate" "BLOCK: debate_quality | 독립 견해 마커 0건" 2>/dev/null
    hook_incident "hook_block" "send_gate" "" "토론 품질: 반론/대안/독립견해 0건" 2>/dev/null || true
    echo '{"decision":"block","reason":"[토론 품질 게이트] 독립 견해(반론/대안/내 판단) 없이 GPT에 전송할 수 없습니다. 반론, 대안, 또는 독립 판단을 최소 1건 포함하세요."}'
    exit 0
  fi
fi

# 통과 — gate 파일 삭제 (1회성)
rm -f "$GATE_FILE"
exit 0
