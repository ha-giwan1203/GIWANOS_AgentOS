#!/bin/bash
# pruning_observe.sh — 세션77 Step 1 Phase 2 관찰 리포트
#
# 목적:
#   격리 후보 7섹션 (24b, 33, 34, 36, 37, 38, 39)의 1주 관찰 결과 집계.
#   실행 빈도(nightly_capability_log.jsonl) + 실패 이력(incident_ledger.jsonl) 종합.
#
# 등급: measurement (read-only, 집계 전용)
#
# 사용법:
#   bash .claude/hooks/pruning_observe.sh                # 최근 7일 리포트
#   bash .claude/hooks/pruning_observe.sh --days 14      # 14일 리포트
#
# Phase 3 (실제 격리 삭제) 진입 조건:
#   - nightly_capability 실행 ≥ 7회 (최소 1주 관찰)
#   - 격리 후보 섹션 FAIL 0
#   - 관련 hook incident 증가 없음

set -u

# Windows Git Bash cp949 방지
export PYTHONIOENCODING=utf-8
export LC_ALL=en_US.UTF-8

# 세션93 (2026-04-22 auto-fix A-2): python3 fallback
PY_CMD="python"
command -v python3 >/dev/null 2>&1 && PY_CMD="python3"

DAYS=7
for arg in "$@"; do
  case "$arg" in
    --days) shift; DAYS="$1"; shift ;;
    --days=*) DAYS="${arg#--days=}" ;;
  esac
done

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"

# Python은 Windows native 경로를 요구 (MSYS /c/... 인식 불가)
if command -v cygpath >/dev/null 2>&1; then
  PROJECT_DIR_PY=$(cygpath -w "$PROJECT_DIR" | sed 's|\\|/|g')
else
  PROJECT_DIR_PY="$PROJECT_DIR"
fi

CANDIDATES_FILE="$PROJECT_DIR_PY/.claude/docs/smoke_test_pruning_candidates.json"
NIGHTLY_LOG="$PROJECT_DIR_PY/.claude/state/nightly_capability_log.jsonl"
INCIDENT_FILE="$PROJECT_DIR_PY/.claude/incident_ledger.jsonl"

if [ ! -f "$CANDIDATES_FILE" ]; then
  echo "[ERROR] pruning candidates 미존재: $CANDIDATES_FILE" >&2
  exit 1
fi

echo "=== Pruning Phase 2 Observation Report ==="
echo "생성 시각: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "관찰 기간: 최근 ${DAYS}일"
echo ""

# ------ 1. 격리 후보 섹션 목록 ------
echo "--- 격리 후보 섹션 (quarantine_*) ---"
"$PY_CMD" -c "
import json
with open('$CANDIDATES_FILE', encoding='utf-8') as f:
    data = json.load(f)
quarantine = [c for c in data if c['status'].startswith('quarantine')]
print(f'총 {len(quarantine)}섹션:')
for c in quarantine:
    print(f'  sec {c[\"num\"]:<4} checks={c[\"check_count\"]:>2}  {c[\"title\"]}')
" || echo "[ERROR] candidates JSON 파싱 실패 (rc=$?)"
echo ""

# ------ 2. nightly_capability 실행 이력 ------
echo "--- nightly_capability_check 실행 이력 ---"
if [ -f "$NIGHTLY_LOG" ]; then
  TOTAL_ENTRIES=$(wc -l < "$NIGHTLY_LOG")
  "$PY_CMD" -c "
import json, datetime
since_days = $DAYS
now = datetime.datetime.utcnow()
threshold = now - datetime.timedelta(days=since_days)
entries = []
with open('$NIGHTLY_LOG', encoding='utf-8') as f:
    for line in f:
        try:
            d = json.loads(line)
            ts = d.get('ts','')
            try:
                dt = datetime.datetime.strptime(ts, '%Y-%m-%dT%H:%M:%SZ')
            except: continue
            if dt < threshold: continue
            entries.append(d)
        except: pass
print(f'총 기록: $TOTAL_ENTRIES건 (파일 전체)')
print(f'최근 {since_days}일 이내: {len(entries)}건')
if entries:
    pass_count = sum(1 for e in entries if e.get('exit_code')==0)
    fail_count = sum(1 for e in entries if e.get('exit_code')!=0)
    avg_dur = sum(e.get('duration_sec',0) for e in entries) / max(len(entries),1)
    print(f'  PASS: {pass_count} / FAIL: {fail_count} / 평균 {avg_dur:.0f}초')
    for e in entries[-5:]:
        print(f'  [{e.get(\"ts\",\"\")}] pass={e.get(\"pass\")}/{e.get(\"total\")} fail={e.get(\"fail\")} ({e.get(\"duration_sec\",0)}s)')
" 2>/dev/null
else
  echo "  [INFO] nightly_capability_log.jsonl 없음 — nightly_capability_check 미등록 또는 미실행"
  echo "  Windows schtasks 등록: .claude/hooks/nightly_capability_check.sh 상단 주석 참조"
fi
echo ""

# ------ 3. 관련 hook incident 집계 (최근 DAYS일) ------
echo "--- 격리 후보 관련 incident (incident_ledger, 최근 ${DAYS}일) ---"
if [ -f "$INCIDENT_FILE" ]; then
  "$PY_CMD" -c "
import json, datetime
from collections import Counter
since_days = $DAYS
now = datetime.datetime.utcnow()
threshold = now - datetime.timedelta(days=since_days)
relevant_keywords = ['incident_review.py','classify_feedback.py','incident_repair.py','task_runner.sh','hook_config.json','json_escape']
matches = []
with open('$INCIDENT_FILE', encoding='utf-8') as f:
    for line in f:
        try:
            d = json.loads(line)
            ts = d.get('ts','')
            try: dt = datetime.datetime.strptime(ts, '%Y-%m-%dT%H:%M:%SZ')
            except: continue
            if dt < threshold: continue
            detail = d.get('detail','') + ' ' + d.get('hook','')
            if any(k in detail for k in relevant_keywords):
                matches.append(d)
        except: pass
print(f'관련 incident: {len(matches)}건')
if matches:
    reasons = Counter(d.get('classification_reason','(none)') for d in matches)
    print(f'분류:')
    for k,v in reasons.most_common(): print(f'  {v:3d}  {k}')
    print(f'최근 5건:')
    for d in matches[-5:]:
        print(f'  [{d.get(\"ts\",\"\")}] {d.get(\"hook\",\"\")}: {d.get(\"detail\",\"\")[:70]}')
else:
    print('  [OK] 관련 incident 0건 — 격리 후보 섹션 안정')
" 2>/dev/null
else
  echo "  [INFO] incident_ledger.jsonl 없음"
fi
echo ""

# ------ 4. Phase 3 진입 판정 ------
echo "--- Phase 3 진입 조건 판정 ---"
if [ ! -f "$NIGHTLY_LOG" ]; then
  echo "  [HOLD] nightly_capability 로그 없음 — 관찰 시작 불가. nightly_capability_check.sh 등록 먼저"
else
  ENTRY_COUNT=$(wc -l < "$NIGHTLY_LOG")
  if [ "$ENTRY_COUNT" -lt 7 ]; then
    echo "  [HOLD] nightly 실행 ${ENTRY_COUNT}회 < 7회 — 관찰 연장"
  else
    echo "  [READY] nightly 실행 ${ENTRY_COUNT}회 ≥ 7회 — incident/FAIL 조건 충족 시 Phase 3 진입 가능"
  fi
fi
echo ""
echo "=== Observation 완료 ==="
