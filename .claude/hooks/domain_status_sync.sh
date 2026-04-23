#!/bin/bash
# domain_status_sync.sh — 도메인 STATUS.md drift advisory
#
# 세션98 2자 토론(debate_20260423_193314) 의제2 C2 합의 산출.
# 전역 TASKS.md 최종 업데이트 날짜와 각 도메인 STATUS.md 날짜 비교 → 14일+ drift 감지 시
# stderr 1줄 경고. 세션 차단 없음 (fail-open / advisory 등급).
#
# 배경: final_check.sh가 전역 90_공통기준/업무관리/STATUS.md만 동기화하고 도메인 STATUS
# 5개는 자동 감시 대상에서 빠져 있었음. Explore 3병렬 스캔에서 02/04/06 12일, 05 17일,
# 10 23일 drift 실측. "1 Problem ↔ 1 Hook" 원칙에 따라 final_check 확장(C1) 대신 전용 훅 신설.
# 30일 실측 후 gate 승격 여부 재평가 (DESIGN_PRINCIPLES 원칙 4 TTL).
#
# 훅 등급: advisory (exit 0 강제, 차단 없음)
# 호출 위치: session_start_restore.sh 마지막 (doctor_lite / token_threshold_check와 동일 패턴)

source "$(dirname "$0")/hook_common.sh" 2>/dev/null || true
_DSS_START=$(hook_timing_start 2>/dev/null || echo 0)

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
GLOBAL_TASKS="$PROJECT_ROOT/90_공통기준/업무관리/TASKS.md"

# 도메인 STATUS 감시 대상 (세션98 Explore 스캔 결과 기준)
DOMAINS=(
  "02_급여단가"
  "04_생산계획"
  "05_생산실적/조립비정산"
  "06_생산관리"
  "10_라인배치"
)

THRESHOLD_DAYS=14

if [ ! -f "$GLOBAL_TASKS" ]; then
  hook_timing_end "domain_status_sync" "$_DSS_START" "no_tasks" 2>/dev/null || true
  exit 0
fi

# TASKS 최종 업데이트 날짜 추출 (final_check와 동일 정규식)
TASKS_DATE=$(sed -n 's/.*최종 업데이트:[[:space:]]*\([0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}\).*/\1/p' "$GLOBAL_TASKS" | head -1)
if [ -z "$TASKS_DATE" ]; then
  hook_timing_end "domain_status_sync" "$_DSS_START" "no_tasks_date" 2>/dev/null || true
  exit 0
fi

# date → epoch (GNU / BSD 양쪽 호환)
to_epoch() {
  date -d "$1" +%s 2>/dev/null || date -j -f "%Y-%m-%d" "$1" +%s 2>/dev/null || echo ""
}

TASKS_EPOCH=$(to_epoch "$TASKS_DATE")
if [ -z "$TASKS_EPOCH" ]; then
  hook_timing_end "domain_status_sync" "$_DSS_START" "epoch_fail" 2>/dev/null || true
  exit 0
fi

THRESHOLD_SECONDS=$((THRESHOLD_DAYS * 86400))
DRIFT_LIST=""

for domain in "${DOMAINS[@]}"; do
  STATUS_FILE="$PROJECT_ROOT/$domain/STATUS.md"
  [ ! -f "$STATUS_FILE" ] && continue

  # 파일 내 모든 YYYY-MM-DD 중 최신(최대값) 선택.
  # ISO-8601 문자열은 lexical sort가 chronological sort와 동일.
  # "최종 업데이트: X / Y (세션98 점검 Z)" 같이 여러 날짜 혼재 시 Z를 우선.
  DOMAIN_DATE=$(grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' "$STATUS_FILE" | sort -r | head -1)
  [ -z "$DOMAIN_DATE" ] && continue

  DOMAIN_EPOCH=$(to_epoch "$DOMAIN_DATE")
  [ -z "$DOMAIN_EPOCH" ] && continue

  DIFF=$((TASKS_EPOCH - DOMAIN_EPOCH))
  if [ "$DIFF" -gt "$THRESHOLD_SECONDS" ]; then
    DIFF_DAYS=$((DIFF / 86400))
    DRIFT_LIST="${DRIFT_LIST}${DRIFT_LIST:+, }${domain}(${DIFF_DAYS}일)"
  fi
done

if [ -n "$DRIFT_LIST" ]; then
  echo "[domain_status_sync] STATUS drift ≥${THRESHOLD_DAYS}일: $DRIFT_LIST" >&2
  hook_log "domain_status_sync" "drift: $DRIFT_LIST" 2>/dev/null || true
fi

hook_timing_end "domain_status_sync" "$_DSS_START" "ok" 2>/dev/null || true
exit 0
