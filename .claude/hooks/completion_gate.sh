#!/bin/bash
# completion-gate v8: 강한 완료 표현만 트리거 + 약한 패턴은 후속 조건
# v7 대비: is_completion_claim 패턴 축소(과감지 86.5% 해소), 약한 패턴 로그만
# GPT+Claude 토론 합의 2026-04-11 세션12
source "$(dirname "$0")/hook_common.sh" 2>/dev/null
# 훅 등급: measurement (Phase 2-C 2026-04-19 세션73 timing 배선 — 소프트 블록 포함이지만 하드페일 없음)
_CMG_START=$(hook_timing_start)
hook_log "Stop" "completion_gate v8" 2>/dev/null || true

MARKER="$STATE_AGENT_CONTROL/write_marker.json"
LEGACY_MARKER="$STATE_AGENT_CONTROL/write_marker.flag"

# 레거시 .flag → .json 마이그레이션
if [ -f "$LEGACY_MARKER" ] && [ ! -f "$MARKER" ]; then
  local_ts=$(date '+%Y-%m-%d %H:%M:%S' 2>/dev/null)
  printf '{"source_file":"unknown","source_class":"unknown","created_at":"%s","after_state_sync":false,"session_key":"%s"}\n' \
    "$local_ts" "$(session_key)" > "$MARKER" 2>/dev/null
  rm -f "$LEGACY_MARKER" 2>/dev/null
fi
TASKS="$PATH_TASKS"
HANDOFF="$PATH_HANDOFF"
STATUS="$PATH_STATUS"

# 마지막 assistant 메시지가 "강한 완료 주장"일 때만 gate 적용
LAST_TEXT=$(last_assistant_text 2>/dev/null || true)
if ! is_completion_claim "$LAST_TEXT"; then
  # 약한 패턴(잔여이슈없음/ALL CLEAR/GPT PASS)만 매칭 시 로그만 남기고 통과
  WEAK_MATCH=$(echo "$LAST_TEXT" | grep -oiE "$_COMPLETION_WEAK_PATTERN" | head -1)
  if [ -n "$WEAK_MATCH" ]; then
    hook_log "Stop" "completion_gate: weak_only pattern='$WEAK_MATCH' — skip" 2>/dev/null
  fi
  hook_timing_end "completion_gate" "$_CMG_START" "skip_noclaim"
  exit 0
fi

# 완료 주장인데 Git 실물 변경이 남아 있으면 먼저 차단
if git_has_relevant_changes; then
  CHANGES=$(git_relevant_change_list | head -n 3 | paste -sd, -)
  hook_incident "gate_reject" "completion_gate" "$CHANGES" "Git 미반영 변경이 남은 상태에서 완료 주장" '"classification_reason":"completion_before_git","next_action":"relevant change를 commit/push 또는 정리한 뒤 완료 보고 재시도"' 2>/dev/null || true
  _CC_TS=$(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S')
  printf '{"ts":"%s","result":"block","reason":"completion_before_git","source":"gate"}\n' "$_CC_TS" \
    >> "$PROJECT_ROOT/.claude/logs/completion_claim.jsonl" 2>/dev/null
  echo "{\"decision\":\"deny\",\"reason\":\"[COMPLETION GATE] Git 실물 변경이 아직 남아 있습니다: ${CHANGES}. 커밋/정리 후 완료로 보고하세요.\"}"
  hook_timing_end "completion_gate" "$_CMG_START" "block_git"
  exit 0
fi

# write_marker 없으면 TASKS/HANDOFF 갱신 gate는 통과
if [ ! -f "$MARKER" ]; then
  hook_timing_end "completion_gate" "$_CMG_START" "skip_nomarker"
  exit 0
fi

# JSON 마커 읽기 — after_state_sync=true면 상태문서 갱신 완료이므로 즉시 통과
MARKER_CONTENT=$(cat "$MARKER" 2>/dev/null)
AFTER_SYNC=$(echo "$MARKER_CONTENT" | safe_json_get "after_state_sync" 2>/dev/null)
if [ "$AFTER_SYNC" = "true" ]; then
  MARKER_CLASS=$(echo "$MARKER_CONTENT" | safe_json_get "source_class" 2>/dev/null || echo "unknown")
  hook_log "Stop" "completion_gate PASS: after_state_sync=true (class=$MARKER_CLASS)" 2>/dev/null
  rm -f "$MARKER" 2>/dev/null
  hook_timing_end "completion_gate" "$_CMG_START" "pass_synced"
  exit 0
fi

# marker timestamp (epoch seconds) — fallback: mtime 비교
MARKER_EPOCH=$(file_mtime "$MARKER")

MISSING=""
for NAME_PATH in "TASKS.md:$TASKS" "HANDOFF.md:$HANDOFF" "STATUS.md:$STATUS"; do
  NAME="${NAME_PATH%%:*}"
  FPATH="${NAME_PATH#*:}"
  if [ ! -f "$FPATH" ]; then
    MISSING="${MISSING}${MISSING:+,}$NAME"
    continue
  fi
  FILE_EPOCH=$(file_mtime "$FPATH")
  if [ "$FILE_EPOCH" -lt "$MARKER_EPOCH" ] 2>/dev/null; then
    MISSING="${MISSING}${MISSING:+,}$NAME"
  fi
done

if [ -n "$MISSING" ]; then
  hook_incident "gate_reject" "completion_gate" "$MISSING" "완료 주장 전 ${MISSING} 미갱신" '"classification_reason":"completion_before_state_sync","normal_flow":true,"next_action":"TASKS/HANDOFF/STATUS를 최신 작업 상태로 갱신한 뒤 완료 보고 재시도"' 2>/dev/null || true
  _CC_TS=$(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S')
  printf '{"ts":"%s","result":"block","reason":"completion_before_state_sync","missing":"%s","source":"gate"}\n' "$_CC_TS" "$MISSING" \
    >> "$PROJECT_ROOT/.claude/logs/completion_claim.jsonl" 2>/dev/null
  echo "{\"decision\":\"deny\",\"reason\":\"[COMPLETION GATE] 완료 보고 전 ${MISSING} 갱신이 필요합니다. TASKS/HANDOFF/STATUS를 모두 갱신한 뒤 종료하세요.\"}"
  hook_timing_end "completion_gate" "$_CMG_START" "block_sync"
  exit 0
fi

# 정상 통과 경로 기록
_CC_TS=$(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S')
printf '{"ts":"%s","result":"pass","reason":"state_sync_ok","source":"gate"}\n' "$_CC_TS" \
  >> "$PROJECT_ROOT/.claude/logs/completion_claim.jsonl" 2>/dev/null
rm -f "$MARKER" 2>/dev/null

# ============================================================================
# Phase 2-B 소프트 블록 (의제5 3자 토론 합의, 2026-04-19)
# 최근 7일간 permissions_sanity '1회용 패턴' 경고가 동일 라벨 3회 이상 누적된 경우
# 완료 보고 직전에 한 번 차단. 하드페일 없음 — 사용자가 의식적으로 재시도하면 통과.
# ============================================================================
PSCOUNT_CACHE="$PROJECT_ROOT/.claude/state/completion_gate_phase2b_last.txt"
_P2B_NOW=$(date +%s 2>/dev/null || echo 0)
_P2B_LAST=0
if [ -f "$PSCOUNT_CACHE" ]; then
  _P2B_LAST=$(cat "$PSCOUNT_CACHE" 2>/dev/null || echo 0)
fi
# 동일 세션에서 이미 경고 후 재시도한 경우는 통과 (60초 이내 재호출 = 사용자 의도적 재시도)
if [ $((_P2B_NOW - _P2B_LAST)) -lt 60 ] 2>/dev/null; then
  hook_timing_end "completion_gate" "$_CMG_START" "pass_cooldown"
  exit 0
fi

if [ -f "$PROJECT_ROOT/.claude/hooks/hook_log.jsonl" ]; then
  REPEATED=$(PYTHONUTF8=1 python3 - "$PROJECT_ROOT/.claude/hooks/hook_log.jsonl" <<'PYEOF' 2>/dev/null
import json, re, sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

log_path = Path(sys.argv[1])
if not log_path.exists():
    sys.exit(0)

cutoff = datetime.now(timezone.utc) - timedelta(days=7)
label_re = re.compile(r'\[([^\]]+)\]')
counter = Counter()

try:
    for line in log_path.read_text(encoding='utf-8', errors='ignore').splitlines():
        try:
            d = json.loads(line)
        except Exception:
            continue
        msg = d.get('msg', '')
        if 'permissions_sanity' not in msg or '경고' not in msg:
            continue
        ts = d.get('ts', '')
        try:
            dt = datetime.strptime(ts, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
        except Exception:
            continue
        if dt < cutoff:
            continue
        m = label_re.search(msg)
        if m:
            counter[m.group(1)] += 1
except Exception:
    sys.exit(0)

repeated = sorted([(k, v) for k, v in counter.items() if v >= 3], key=lambda x: -x[1])
if repeated:
    parts = [f"{k}({v}회)" for k, v in repeated[:3]]
    print("|".join(parts))
PYEOF
)
  if [ -n "$REPEATED" ]; then
    hook_incident "soft_block" "completion_gate" "$REPEATED" "1회용 패턴 ${REPEATED} 7일 내 3회 이상 누적" '"classification_reason":"oneoff_pattern_repeat","phase":"2B","next_action":"CLAUDE.md 5단계 의사결정 트리 참조. 포괄 Bash(echo:*) 등 사용 또는 settings 정리 후 재보고"' 2>/dev/null || true
    printf '{"ts":"%s","result":"soft_block","reason":"phase2b_oneoff_repeat","repeated":"%s","source":"gate"}\n' "$_CC_TS" "$REPEATED" \
      >> "$PROJECT_ROOT/.claude/logs/completion_claim.jsonl" 2>/dev/null
    echo "$_P2B_NOW" > "$PSCOUNT_CACHE" 2>/dev/null || true
    echo "{\"decision\":\"deny\",\"reason\":\"[COMPLETION GATE · Phase 2-B 소프트 블록] 최근 7일간 permissions 1회용 패턴이 반복 등록되고 있습니다: ${REPEATED}. CLAUDE.md 5단계 의사결정 트리를 재검토하거나 포괄 Bash(echo:*) 패턴을 활용하세요. 의도적인 진행이라면 재보고 시 통과됩니다(60초 쿨다운).\"}"
    hook_timing_end "completion_gate" "$_CMG_START" "soft_block"
    exit 0
  fi
fi

hook_timing_end "completion_gate" "$_CMG_START" "pass"
exit 0
