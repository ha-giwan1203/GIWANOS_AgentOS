#!/bin/bash
# Self-X Layer 2 — T1 자동 복구 (Stop hook)
# 출처: debate_20260421_151042_3way (B2 3way 만장일치)
# 등급: advisory (실패해도 세션 종료, exit 0). hard 차단 없음.
# 정책: T1만 (T2는 1-click 승인 필요), idempotent, jsonl append-only

set +e

source "$(dirname "$0")/hook_common.sh"
_RT1_START=$(hook_timing_start)

CB_FILE="$PROJECT_ROOT/.claude/self/circuit_breaker.json"
RECOVERY_LOG="$PROJECT_ROOT/.claude/self/auto_recovery.jsonl"

# Circuit Breaker 잠금 상태면 T1 실행 X (B4 정책)
if [ -f "$CB_FILE" ]; then
  LOCKED=$(PYTHONIOENCODING=utf-8 timeout 2 python3 -c "
import json
try:
    s = json.load(open('$CB_FILE', encoding='utf-8'))
    print('1' if s.get('state', {}).get('locked', False) else '0')
except: print('0')
" 2>/dev/null)
  if [ "$LOCKED" = "1" ]; then
    echo "[self-recovery-t1] Circuit Breaker 잠금 — T1 실행 건너뜀" >&2
    hook_log "self_recovery_t1" "skipped circuit_breaker_locked"
    hook_timing_end "self_recovery_t1" "$_RT1_START" "advisory"
    exit 0
  fi
fi

# T1 일일 상한 검사 (B4: 6건)
TODAY=$(date "+%Y-%m-%d")
DAILY_COUNT=0
if [ -f "$RECOVERY_LOG" ]; then
  DAILY_COUNT=$(grep "\"date\": \"$TODAY\"" "$RECOVERY_LOG" 2>/dev/null | wc -l)
fi
if [ "$DAILY_COUNT" -ge 6 ]; then
  hook_log "self_recovery_t1" "daily limit reached ($DAILY_COUNT)"
  hook_timing_end "self_recovery_t1" "$_RT1_START" "advisory"
  exit 0
fi

# T1 항목 1: log rotation (hook_log >512KB)
HOOK_LOG_FILE="$PROJECT_ROOT/.claude/hooks/hook_log.jsonl"
if [ -f "$HOOK_LOG_FILE" ]; then
  SIZE=$(stat -c%s "$HOOK_LOG_FILE" 2>/dev/null || echo 0)
  if [ "$SIZE" -gt 524288 ]; then
    mv "$HOOK_LOG_FILE" "$HOOK_LOG_FILE.$(date +%Y%m%d_%H%M%S)" 2>/dev/null
    touch "$HOOK_LOG_FILE"
    echo "{\"ts\":\"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\",\"date\":\"$TODAY\",\"action\":\"log_rotation\",\"target\":\"hook_log.jsonl\",\"size\":$SIZE}" >> "$RECOVERY_LOG"
  fi
fi

# T1 항목 2: archive_resolved + auto_resolve + backfill_classification (incident_repair 재사용)
INCIDENT_REPAIR="$PROJECT_ROOT/.claude/hooks/incident_repair.py"
if [ -f "$INCIDENT_REPAIR" ]; then
  # 결정적 작업 (실패 가중치 1.0): 1회 재시도
  for ATTEMPT in 1 2; do
    OUT=$(PYTHONIOENCODING=utf-8 timeout 10 python3 "$INCIDENT_REPAIR" --auto-resolve 2>&1)
    RC=$?
    if [ "$RC" -eq 0 ]; then
      RESOLVED=$(echo "$OUT" | grep -oE '[0-9]+' | head -1)
      if [ -n "$RESOLVED" ] && [ "$RESOLVED" -gt 0 ]; then
        echo "{\"ts\":\"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\",\"date\":\"$TODAY\",\"action\":\"auto_resolve\",\"resolved\":$RESOLVED}" >> "$RECOVERY_LOG"
      fi
      break
    fi
    [ "$ATTEMPT" -eq 2 ] && echo "{\"ts\":\"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\",\"date\":\"$TODAY\",\"action\":\"auto_resolve\",\"status\":\"failed\",\"weight\":1.0}" >> "$RECOVERY_LOG"
  done

  # backfill_classification (idempotent)
  OUT=$(PYTHONIOENCODING=utf-8 timeout 10 python3 "$INCIDENT_REPAIR" --backfill-classification 2>&1)
  RC=$?
  if [ "$RC" -eq 0 ]; then
    BF=$(echo "$OUT" | grep -oE '[0-9]+' | head -1)
    if [ -n "$BF" ] && [ "$BF" -gt 0 ]; then
      echo "{\"ts\":\"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\",\"date\":\"$TODAY\",\"action\":\"backfill_classification\",\"backfilled\":$BF}" >> "$RECOVERY_LOG"
    fi
  fi

  # archive_resolved (resolved 30d+) — 청소 작업 (실패 가중치 0.5, 재시도 0회)
  OUT=$(PYTHONIOENCODING=utf-8 timeout 10 python3 "$INCIDENT_REPAIR" --archive 2>&1)
  RC=$?
  if [ "$RC" -eq 0 ]; then
    AR=$(echo "$OUT" | grep -oE '[0-9]+' | head -1)
    if [ -n "$AR" ] && [ "$AR" -gt 0 ]; then
      echo "{\"ts\":\"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\",\"date\":\"$TODAY\",\"action\":\"archive_resolved\",\"archived\":$AR}" >> "$RECOVERY_LOG"
    fi
  else
    echo "{\"ts\":\"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\",\"date\":\"$TODAY\",\"action\":\"archive_resolved\",\"status\":\"failed\",\"weight\":0.5}" >> "$RECOVERY_LOG"
  fi
fi

hook_log "self_recovery_t1" "completed daily=$DAILY_COUNT"
hook_timing_end "self_recovery_t1" "$_RT1_START" "advisory"
exit 0
