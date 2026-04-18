#!/bin/bash
# evidence_missing incident 원인별 집계 스크립트
# GPT 세션65 토론 합의(20260418_113219): 일자별 + 원인 버킷 집계
# 사용법: .claude/scripts/evidence_missing_stats.sh [cutoff_iso]
#   - cutoff_iso 미지정 시 전체 집계만 출력
#   - cutoff_iso 지정 시 전/후 7일 비교 (예: 2026-04-18T02:13:00Z)
#
# 임계값 판정 (GPT 합의):
#   배포 후 7일 총합 ≤ 50   → 5조건 보류
#   51~70                   → 1주 연장 관찰
#   71+ or 감소율 < 60%     → 5조건 즉시 구현

set -e
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LEDGER="$PROJECT_ROOT/.claude/incident_ledger.jsonl"
CUTOFF="${1:-}"

if [ ! -f "$LEDGER" ]; then
  echo "ERROR: ledger 없음: $LEDGER" >&2
  exit 1
fi

extract_cause() {
  # detail 필드에서 원인 버킷 추출
  # - map_scope      : map_scope.req
  # - tasks_handoff  : TASKS/HANDOFF 갱신 관련
  # - skill_read     : SKILL.md / identifier_ref
  # - auth_diag      : MES/OAuth
  # - date_check     : date_check.req
  # - skill_instr    : skill_instruction_gate
  # - other          : 나머지
  local detail="$1"
  local hook="$2"
  case "$detail" in
    *"map_scope"*) echo "map_scope" ;;
    *"tasks_handoff"*|*"TASKS/HANDOFF 갱신"*) echo "tasks_handoff" ;;
    *"skill_read"*|*"identifier_ref"*|*"SKILL.md"*) echo "skill_read" ;;
    *"auth_diag"*|*"MES/OAuth"*|*"MES access"*) echo "auth_diag" ;;
    *"date_check"*) echo "date_check" ;;
    *)
      case "$hook" in
        *"skill_instruction_gate"*) echo "skill_instr" ;;
        *) echo "other" ;;
      esac
      ;;
  esac
}

parse_lines() {
  local from="$1"  # ISO timestamp, empty = no filter
  local until="$2"
  awk -v from="$from" -v until="$until" '
    BEGIN { FS=""; }
    /evidence_missing/ {
      # ts 추출
      match($0, /"ts":"[^"]+"/);
      ts = substr($0, RSTART+6, RLENGTH-7);
      # detail 추출
      match($0, /"detail":"[^"]+"/);
      detail = substr($0, RSTART+10, RLENGTH-11);
      # hook 추출
      match($0, /"hook":"[^"]+"/);
      hook = substr($0, RSTART+8, RLENGTH-9);
      # 필터
      if (from != "" && ts < from) next;
      if (until != "" && ts >= until) next;
      print ts "\t" hook "\t" detail;
    }
  ' "$LEDGER"
}

print_bucket_table() {
  local label="$1"; shift
  local from="$1"; shift
  local until="$1"; shift

  echo ""
  echo "=== $label ==="
  if [ -n "$from" ]; then echo "기간: $from ~ ${until:-현재}"; fi

  local total=0
  declare -A buckets
  while IFS=$'\t' read -r ts hook detail; do
    [ -z "$ts" ] && continue
    local cause
    cause=$(extract_cause "$detail" "$hook")
    buckets[$cause]=$((${buckets[$cause]:-0} + 1))
    total=$((total + 1))
  done < <(parse_lines "$from" "$until")

  printf "%-15s %5s\n" "원인버킷" "건수"
  printf "%-15s %5s\n" "---------------" "-----"
  for cause in map_scope tasks_handoff skill_read auth_diag date_check skill_instr other; do
    printf "%-15s %5d\n" "$cause" "${buckets[$cause]:-0}"
  done
  printf "%-15s %5s\n" "---------------" "-----"
  printf "%-15s %5d\n" "TOTAL" "$total"

  echo "$total"  # 반환용 (마지막 줄 파싱)
}

echo "evidence_missing 집계 스크립트"
echo "실행시각: $(date '+%Y-%m-%d %H:%M:%S KST')"
echo "ledger: $LEDGER (총 $(wc -l < "$LEDGER")행)"

if [ -z "$CUTOFF" ]; then
  # 전체 집계 + 최근 7일
  NOW_ISO=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
  D7_ISO=$(date -u -d '7 days ago' '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || \
           python3 -c "from datetime import datetime, timedelta, timezone; print((datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ'))")

  print_bucket_table "전체 기간" "" "" > /dev/null
  print_bucket_table "최근 7일 ($D7_ISO ~)" "$D7_ISO" ""
else
  # 전/후 비교 모드
  PRE_START=$(date -u -d "$CUTOFF - 7 days" '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || \
              python3 -c "from datetime import datetime, timedelta, timezone; c=datetime.fromisoformat('$CUTOFF'.replace('Z','+00:00')); print((c - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ'))")
  POST_END=$(date -u -d "$CUTOFF + 7 days" '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || \
             python3 -c "from datetime import datetime, timedelta, timezone; c=datetime.fromisoformat('$CUTOFF'.replace('Z','+00:00')); print((c + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ'))")

  # 배포 후 경과 시간 계산 (provisional 표시용)
  NOW_EPOCH=$(date -u +%s)
  CUTOFF_EPOCH=$(date -u -d "$CUTOFF" +%s 2>/dev/null || \
                 python3 -c "from datetime import datetime, timezone; print(int(datetime.fromisoformat('$CUTOFF'.replace('Z','+00:00')).timestamp()))")
  ELAPSED_SEC=$((NOW_EPOCH - CUTOFF_EPOCH))
  ELAPSED_HOURS=$((ELAPSED_SEC / 3600))
  FULL_WINDOW=$((7 * 24))
  IS_PROVISIONAL=false
  if [ "$ELAPSED_HOURS" -lt "$FULL_WINDOW" ] 2>/dev/null; then
    IS_PROVISIONAL=true
    POST_LABEL="배포 후 경과 구간 (${ELAPSED_HOURS}h / 168h — provisional)"
  else
    POST_LABEL="배포 후 7일"
  fi

  PRE_OUT=$(print_bucket_table "배포 전 7일" "$PRE_START" "$CUTOFF")
  POST_OUT=$(print_bucket_table "$POST_LABEL" "$CUTOFF" "$POST_END")
  echo "$PRE_OUT"
  echo "$POST_OUT"

  PRE_TOTAL=$(echo "$PRE_OUT" | tail -1)
  POST_TOTAL=$(echo "$POST_OUT" | tail -1)

  echo ""
  echo "=== 판정 (GPT 세션65 합의) ==="
  echo "배포 전 7일: $PRE_TOTAL 건"
  echo "$POST_LABEL: $POST_TOTAL 건"

  RATE=""
  if [ "$PRE_TOTAL" -gt 0 ] 2>/dev/null; then
    RATE=$(awk -v pre="$PRE_TOTAL" -v post="$POST_TOTAL" 'BEGIN{printf "%.1f", (pre-post)*100/pre}')
    echo "감소율: ${RATE}%"
  fi

  if [ "$IS_PROVISIONAL" = "true" ]; then
    echo "판정: provisional — 7일 경과 후 최종 판정 (현재 ${ELAPSED_HOURS}h 경과)"
    echo "  조기신호: POST=$POST_TOTAL, RATE=${RATE:-N/A}%"
  else
    # 7일 경과 완료 — GPT 임계값 적용
    # 감소율<60% 분기 포함 (세션65 GPT 5-0 지적 반영)
    RATE_NUM=$(awk -v r="${RATE:-0}" 'BEGIN{printf "%d", r}')
    if [ "$POST_TOTAL" -ge 71 ] 2>/dev/null || [ "$RATE_NUM" -lt 60 ] 2>/dev/null; then
      echo "판정: 5조건 즉시 구현 (POST ≥ 71 또는 감소율 < 60%)"
    elif [ "$POST_TOTAL" -le 50 ] 2>/dev/null; then
      echo "판정: 5조건 보류 (POST ≤ 50)"
    else
      echo "판정: 1주 연장 관찰 (51 ≤ POST ≤ 70)"
    fi
  fi
fi

exit 0
