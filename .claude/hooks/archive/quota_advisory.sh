#!/bin/bash
# Self-X Layer 2/4 — Subtraction Quota advisory (commit 시점)
# 출처: debate_20260421_142204_3way (B5 만장일치)
# 등급: advisory (commit 통과, WARN 누적). hard 차단은 별도 통합 후속.
#
# 동작: PostToolUse Bash matcher (git commit*) → quota 상태 1줄 보고 + 100% 도달 시 경고

set +e

source "$(dirname "$0")/hook_common.sh"
_QA_START=$(hook_timing_start)

INPUT=$(cat 2>/dev/null)

# tool_input.command 추출 (jq 없이 grep)
if ! echo "$INPUT" | grep -qE '"command"\s*:\s*"[^"]*git\s+commit'; then
  hook_timing_end "quota_advisory" "$_QA_START" "advisory"
  exit 0
fi

# quota_diagnose 실행 (timeout 5s)
if [ -f "$PROJECT_ROOT/.claude/self/quota_diagnose.py" ]; then
  RESULT=$(PYTHONIOENCODING=utf-8 timeout 3 python3 "$PROJECT_ROOT/.claude/self/quota_diagnose.py" --json --quick 2>/dev/null)
  if [ -n "$RESULT" ]; then
    # 핵심 1줄 추출
    SUMMARY=$(echo "$RESULT" | python3 -c "
import json, sys
try:
    p = json.load(sys.stdin)
    q = p['quota']
    h = q['hook']
    raw, active, target = h['raw'], h['active'], h.get('active_target', 0)
    if isinstance(target, int) and target > 0:
        pct = int(active * 100 / target)
        status = 'OK' if active <= target else 'OVER'
        print(f'[quota] hook raw={raw} active={active}/{target} ({pct}% {status})')
        if active > target:
            print('  [WARN] 활성 hook 정원 초과 — 1 in 1 out 권장. 면제: [bypass-quota] 태그')
        cands = [c for c in p.get('candidates', []) if c['class'] == '즉시삭제후보']
        if cands:
            print(f'  → 즉시삭제 후보 {len(cands)}건: 90_공통기준/protected_assets.yaml 참조')
except Exception as e:
    print(f'[quota] eval 실패: {e}')
")
    if [ -n "$SUMMARY" ]; then
      echo "" >&2
      echo "$SUMMARY" >&2
      hook_log "quota_advisory" "summary=$(echo $SUMMARY | head -1)"
    fi
  fi
fi

hook_timing_end "quota_advisory" "$_QA_START" "advisory"
exit 0
