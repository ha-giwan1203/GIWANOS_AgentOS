#!/bin/bash
# Self-X Layer 1 — SessionStart 자가 진단 hook
# 출처: debate_20260421_133506_3way (3way 만장일치 통과 pass_ratio=1.0)
# 등급: measurement (감지만, 차단 없음, exit 0 강제)
# 정책: P2 SessionStart 1회+캐시 / P3 OS timeout 5s / M1 [System Health] stdout 주입

set +e  # advisory: 실패해도 세션 계속

source "$(dirname "$0")/hook_common.sh"
_HC_START=$(hook_timing_start)

DIAGNOSE_SCRIPT="$PROJECT_ROOT/.claude/self/diagnose.py"
HEALTH_FILE="$PROJECT_ROOT/.claude/self/HEALTH.md"
SUMMARY_FILE="$PROJECT_ROOT/.claude/self/summary.txt"

# 입력 처리 (SessionStart hook은 JSON input 받음)
INPUT=$(cat)
SOURCE=$(printf '%s' "$INPUT" | safe_json_get "source" 2>/dev/null || echo "unknown")

# diagnose.py 실행 (1세션 캐시 자동 적용)
if [ -f "$DIAGNOSE_SCRIPT" ]; then
  # P3: OS timeout 5초 격리, P2: 캐시 활용
  PYTHONIOENCODING=utf-8 timeout 5 python3 "$DIAGNOSE_SCRIPT" --summary-only > /dev/null 2>&1
  RC=$?

  if [ $RC -eq 124 ]; then
    # timeout
    echo "[System Health] 평가 timeout - WARN" >&2
    hook_log "health_check" "diagnose timeout source=$SOURCE"
  elif [ -f "$SUMMARY_FILE" ]; then
    SUMMARY=$(cat "$SUMMARY_FILE" 2>/dev/null | head -1)
    # M1: [System Health] 블록을 stderr로 출력 (Claude 컨텍스트 강제 주입)
    echo "" >&2
    echo "=== [System Health] ===" >&2
    echo "$SUMMARY" >&2
    # WARN/CRITICAL 시 상세 표시
    if echo "$SUMMARY" | grep -qE "(WARN|CRITICAL)"; then
      echo "  → 상세: .claude/self/HEALTH.md 참조" >&2
      # WARN 3줄 이하, CRITICAL은 모두 표시 (GPT 안)
      ( cd "$PROJECT_ROOT" && PYTHONIOENCODING=utf-8 python3 -c "
import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
try:
    p = json.load(open('.claude/self/last_diagnosis.json', encoding='utf-8'))
    crit = [r for r in p['results'] if r['status'] == 'CRITICAL']
    warn = [r for r in p['results'] if r['status'] == 'WARN']
    for r in crit:
        print(f'  CRITICAL: {r[\"name\"]} - {r[\"message\"]}')
    for r in warn[:3]:
        print(f'  WARN: {r[\"name\"]} - {r[\"message\"]}')
    if len(warn) > 3:
        print(f'  ... +{len(warn)-3} WARN (HEALTH.md 참조)')
except Exception as e:
    print(f'  (상세 로드 실패: {e})')
" >&2 ) 2>&1 >&2
    fi
    echo "=======================" >&2
    echo "" >&2
    hook_log "health_check" "summary=$SUMMARY source=$SOURCE"
  else
    echo "[System Health] 진단 결과 없음" >&2
    hook_log "health_check" "no summary file source=$SOURCE"
  fi
fi

hook_timing_end "health_check" "$_HC_START" "measurement"
exit 0
