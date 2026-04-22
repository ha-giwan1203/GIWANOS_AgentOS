#!/bin/bash
# selfcheck.sh — 주 1회 수동 실행 자기유지 점검 묶음
#
# 세션91 단계 IV-2 (2026-04-22) 신설. 원칙 1 "Meta Depth = 0 (안전안)".
# Self-X 자동 hook 전면 제거 + 수동 selfcheck 전환의 유일한 실행 경로.
#
# 묶음:
#   1. smoke_fast       — 훅 파일·settings·TASKS/HANDOFF·gate_boundary 11건
#   2. doctor_lite      — 설정 건전성 요약
#   3. diagnose.py      — invariants 평가 + HEALTH.md + summary.txt 갱신
#   4. quota_diagnose.py — 실행 표면 정원 카운트 (advisory)
#   5. incident 요약    — 미해결 건수 + 최근 24h 신규
#   6. last_selfcheck   — 실행 타임스탬프 기록
#
# 실행:
#   bash .claude/self/selfcheck.sh
#
# 출력: stdout 요약 + .claude/self/summary.txt / HEALTH.md / last_selfcheck.txt 갱신
#
# 근거: C:/Users/User/.claude/plans/glimmering-churning-reef.md Part 3 단계 IV

set -u

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
SELF_DIR="$PROJECT_DIR/.claude/self"
HOOKS_DIR="$PROJECT_DIR/.claude/hooks"
INCIDENT_LEDGER="$PROJECT_DIR/.claude/incident_ledger.jsonl"
LAST_SELFCHECK="$SELF_DIR/last_selfcheck.txt"

PY_CMD="python"
command -v python3 >/dev/null 2>&1 && PY_CMD="python3"

echo "=== selfcheck (세션91 단계 IV-2) ==="
echo "시작: $(date '+%Y-%m-%d %H:%M:%S KST')"
echo ""

# 1. smoke_fast
echo "--- 1. smoke_fast ---"
bash "$HOOKS_DIR/smoke_fast.sh" 2>&1 | tail -3
echo ""

# 2. doctor_lite
echo "--- 2. doctor_lite ---"
if [ -x "$HOOKS_DIR/doctor_lite.sh" ]; then
  bash "$HOOKS_DIR/doctor_lite.sh" 2>&1 | tail -10
else
  echo "  doctor_lite.sh 없음"
fi
echo ""

# 3. diagnose (invariants + HEALTH.md)
echo "--- 3. diagnose ---"
if [ -x "$SELF_DIR/diagnose.py" ] || [ -f "$SELF_DIR/diagnose.py" ]; then
  "$PY_CMD" "$SELF_DIR/diagnose.py" 2>&1 | tail -5
else
  echo "  diagnose.py 없음 (archive 상태)"
fi
echo ""

# 4. quota
echo "--- 4. quota_diagnose ---"
if [ -x "$SELF_DIR/quota_diagnose.py" ] || [ -f "$SELF_DIR/quota_diagnose.py" ]; then
  "$PY_CMD" "$SELF_DIR/quota_diagnose.py" 2>&1 | tail -5
else
  echo "  quota_diagnose.py 없음 (archive 상태)"
fi
echo ""

# 5. incident 요약
echo "--- 5. incident 요약 ---"
if [ -f "$INCIDENT_LEDGER" ]; then
  TOTAL=$(wc -l < "$INCIDENT_LEDGER" | tr -d ' ')
  RESOLVED=$(grep -c '"resolved":[[:space:]]*true' "$INCIDENT_LEDGER" 2>/dev/null || echo 0)
  UNRESOLVED=$((TOTAL - RESOLVED))
  # 세션93 (2026-04-22 2자 토론 합의, plan.md 1주차 2번):
  # prefix grep (CUTOFF='%Y-%m-%dT%H') → 정확한 timestamp 비교로 교체
  # 기존: "24h 전 그 한 시간대"만 카운트 → 실제 24h 범위 미반영
  # 교체: python으로 ISO8601 파싱 후 current - 24h 이후 모든 incident 카운트
  RECENT=$("$PY_CMD" - "$INCIDENT_LEDGER" <<'PYEOF' 2>/dev/null
import sys, json
from datetime import datetime, timedelta, timezone
cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
count = 0
try:
    with open(sys.argv[1], encoding='utf-8') as f:
        for line in f:
            try:
                ts_str = json.loads(line).get('ts', '')
                if not ts_str:
                    continue
                ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                if ts >= cutoff:
                    count += 1
            except Exception:
                pass
except Exception:
    pass
print(count)
PYEOF
)
  RECENT="${RECENT:-0}"
  echo "  총 $TOTAL건 / 해결 $RESOLVED건 / 미해결 $UNRESOLVED건"
  echo "  최근 24h 신규: ${RECENT}건"
else
  echo "  incident_ledger 없음"
fi
echo ""

# 6. 실행 타임스탬프 기록
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S KST')
echo "마지막 실행: $TIMESTAMP" > "$LAST_SELFCHECK"
echo "=== selfcheck 종료: $TIMESTAMP ==="
