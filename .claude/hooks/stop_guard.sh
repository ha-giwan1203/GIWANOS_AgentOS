#!/bin/bash
# Stop hook — 금지 문구 차단 + 토론모드 필수 형식 검사
# Claude 응답 완료 직전에 실행. 위반 시 exit 2로 stop 차단.
# v2: 마지막 assistant 블록 기준 판정 (GPT 합의 2026-04-01)
source "$(dirname "$0")/hook_common.sh" 2>/dev/null
hook_log "Stop" "stop_guard 발화" 2>/dev/null

# HOOK_LOG는 hook_common.sh의 hook_log() 함수로 통일 (hook_log.jsonl)
TRANSCRIPT="$CLAUDE_TRANSCRIPT_PATH"

if [ -z "$TRANSCRIPT" ] || [ ! -f "$TRANSCRIPT" ]; then
  exit 0
fi

# === 마지막 assistant 메시지의 text content만 추출 ===
# hook_common.sh의 last_assistant_text() 재사용 (safe_json_get 기반, 이스케이프 따옴표 처리)
LAST_TEXT=$(last_assistant_text 2>/dev/null || true)

if [ -z "$LAST_TEXT" ]; then
  exit 0
fi

# === 1. 금지 문구 검사 (마지막 assistant text에서만) ===
FORBIDDEN_PATTERNS=(
  "전송할까요"
  "업데이트할까요"
  "진행할까요"
  "승인해주시면"
  "반영할까요"
  "이렇게 할까요"
  "확인해주시면"
)

for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
  if echo "$LAST_TEXT" | grep -q "$pattern"; then
    hook_log "Stop/stop_guard" "BLOCK: forbidden_phrase | $pattern" 2>/dev/null
    hook_incident "hook_block" "stop_guard" "" "금지 문구: $pattern" '"classification_reason":"stop_guard_block"' 2>/dev/null || true
    echo '{"decision":"block","reason":"[Stop Guard] 금지 문구 감지: '"$pattern"'. 사용자에게 중간 승인을 요청하지 마라. 합의 후 바로 실행하고 결과만 보고해라."}'
    exit 2
  fi
done

# === 2. 토론모드 필수 형식 검사 (마지막 assistant text에서만) ===
if echo "$LAST_TEXT" | grep -qE "하네스 분석|주장 분해|채택.*버림|debate-mode|토론모드"; then
  HAS_ADOPT=$(echo "$LAST_TEXT" | grep -c "채택:")
  HAS_DISCARD=$(echo "$LAST_TEXT" | grep -cE "버림:|보류:")

  if [ "$HAS_ADOPT" -eq 0 ] && [ "$HAS_DISCARD" -eq 0 ]; then
    exit 0  # 토론 문맥이지만 형식 없으면 단순 전달 가능 → 통과
  fi

  if [ "$HAS_DISCARD" -eq 0 ]; then
    hook_log "Stop/stop_guard" "BLOCK: missing_bucket | 보류+버림 0건" 2>/dev/null
    hook_incident "hook_block" "stop_guard" "" "토론모드 보류+버림 0건" '"classification_reason":"stop_guard_block"' 2>/dev/null || true
    echo '{"decision":"block","reason":"[Stop Guard] 토론모드에서 보류/버림이 0건. GPT 프레임을 그대로 수용한 것으로 판단. 주장 분해 → 라벨링 → 채택/보류/버림을 다시 수행하라."}'
    exit 2
  fi
fi

# === 3. 토론모드 독립 견해 백스톱 (GPT 합의 2026-04-07) ===
# send_gate 주력 + stop_guard 백스톱 2중 구성
if echo "$LAST_TEXT" | grep -qE "하네스 분석|주장 분해|채택.*버림|debate-mode|토론모드|\[Claude"; then
  OPINION_MARKERS='(반론|대안|다른 접근|내 판단|Claude 판단|환경상 비적합|내 독립 견해|내 우려)'
  if ! echo "$LAST_TEXT" | grep -qE "$OPINION_MARKERS"; then
    # 단순 보고성 메시지는 제외
    if ! echo "$LAST_TEXT" | grep -qE '(커밋|푸시|SHA|diff|PASS|FAIL|검증 결과|판정 요청|수정 완료)'; then
      hook_log "Stop/stop_guard" "BLOCK: debate_quality_backstop | 독립 견해 0건" 2>/dev/null
      hook_incident "hook_block" "stop_guard" "" "백스톱: 독립 견해 0건" '"classification_reason":"stop_guard_block"' 2>/dev/null || true
      echo '{"decision":"block","reason":"[Stop Guard 백스톱] 토론 응답에 독립 견해(반론/대안/내 판단)가 없습니다. GPT 프레임에 끌려가지 말고 독립 판단을 포함하세요."}'
      exit 2
    fi
  fi
fi

exit 0
