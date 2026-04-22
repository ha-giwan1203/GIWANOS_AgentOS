#!/bin/bash
# Self-X Layer 4 — Circuit Breaker check (advisory)
# 출처: debate_20260421_145810_3way (B4 3way 만장일치)
# 등급: advisory (잠금 발생 시 사용자 승인 프롬프트만, hard 차단 없음)
# 정책: depth=1 하드코딩, self-meta 실패 시 WARN 파일만

set +e

source "$(dirname "$0")/hook_common.sh"
_CB_START=$(hook_timing_start)

CB_FILE="$PROJECT_ROOT/.claude/self/circuit_breaker.json"
META_FILE="$PROJECT_ROOT/.claude/self/meta.json"
META_WARN="$PROJECT_ROOT/.claude/self/meta_warn.log"

# 메타 깊이=1 하드코딩 — 본 hook 자체는 self-meta 평가 금지 (재귀 차단)
# 단순히 circuit_breaker.json 상태 읽고 잠금 시 프롬프트 표시만

if [ ! -f "$CB_FILE" ]; then
  hook_timing_end "circuit_breaker_check" "$_CB_START" "advisory"
  exit 0
fi

LOCKED=$(PYTHONIOENCODING=utf-8 timeout 2 python3 -c "
import json, sys
try:
    s = json.load(open('$CB_FILE', encoding='utf-8'))
    print('1' if s.get('state', {}).get('locked', False) else '0')
except Exception as e:
    sys.stderr.write(f'meta WARN: {e}\n')
    print('0')
" 2>/dev/null)

if [ "$LOCKED" = "1" ]; then
  REASON=$(PYTHONIOENCODING=utf-8 python3 -c "
import json
s = json.load(open('$CB_FILE', encoding='utf-8'))
print(s.get('state', {}).get('locked_reason', 'unknown'))
" 2>/dev/null)
  echo "" >&2
  echo "[circuit-breaker] self-X 잠금 상태 — 자동 변경 차단 중" >&2
  echo "  reason: $REASON" >&2
  echo "  해제: 4개 기준 충족 후 1-click 승인 (.claude/self/circuit_breaker.json 참조)" >&2
  echo "" >&2
  hook_log "circuit_breaker_check" "locked reason=$REASON"
fi

hook_timing_end "circuit_breaker_check" "$_CB_START" "advisory"
exit 0
