#!/bin/bash
# token_threshold_check — 저장소 문서 비대화 사전 감시 (advisory)
# 세션68 2026-04-18 영상분석 3자 토론 합의 (의제2, pass_ratio 1.00)
# 로그: 90_공통기준/토론모드/logs/debate_20260418_164115_3way/
# 등급: advisory (차단 없음, exit 0 강제)

source "$(dirname "$0")/hook_common.sh"
_TTC_START=$(hook_timing_start)

# === 임계치 (합의안 고정) ===
TASKS_WARN=400;          TASKS_STRONG=800
HANDOFF_WARN=500;        HANDOFF_STRONG=800
MEMORY_INDEX_WARN=120;   MEMORY_INDEX_STRONG=200
MEMORY_FILES_WARN=60;    MEMORY_FILES_STRONG=100
INCIDENT_WARN=1048576;   INCIDENT_STRONG=3145728

# === 경로 (테스트 override 허용) ===
_TASKS_PATH="${TOKEN_THRESHOLD_TASKS_OVERRIDE:-$PATH_TASKS}"
_HANDOFF_PATH="${TOKEN_THRESHOLD_HANDOFF_OVERRIDE:-$PATH_HANDOFF}"
_MEMORY_DIR="${TOKEN_THRESHOLD_MEMORY_OVERRIDE:-$HOME/.claude/projects/C--Users-User-Desktop------/memory}"
_INCIDENT_PATH="${TOKEN_THRESHOLD_INCIDENT_OVERRIDE:-$INCIDENT_LEDGER}"

ISSUES=()
STRONG_HITS=()

_measure_lines() {
  # $1=label $2=path $3=warn $4=strong
  local label="$1" path="$2" warn="$3" strong="$4"
  [ -f "$path" ] || return 0
  local n
  n=$(wc -l < "$path" 2>/dev/null | tr -d ' ')
  [ -z "$n" ] && return 0
  if [ "$n" -ge "$strong" ] 2>/dev/null; then
    local cut=$((n - strong))
    ISSUES+=("[STRONG] $label: $n / $strong줄 — 감축 권고: ${cut}줄. /memory-audit 또는 98_아카이브/ 이동 검토")
    STRONG_HITS+=("$label")
  elif [ "$n" -ge "$warn" ] 2>/dev/null; then
    ISSUES+=("[WARN] $label: $n / $warn줄")
  fi
}

_measure_bytes() {
  local label="$1" path="$2" warn="$3" strong="$4"
  [ -f "$path" ] || return 0
  local b
  b=$(wc -c < "$path" 2>/dev/null | tr -d ' ')
  [ -z "$b" ] && return 0
  if [ "$b" -ge "$strong" ] 2>/dev/null; then
    local mb=$((b / 1048576))
    ISSUES+=("[STRONG] $label: ${mb}MB+ / 3MB — incident_repair.py --archive 실행 권장")
    STRONG_HITS+=("$label")
  elif [ "$b" -ge "$warn" ] 2>/dev/null; then
    local kb=$((b / 1024))
    ISSUES+=("[WARN] $label: ${kb}KB / 1MB")
  fi
}

_measure_memory_files() {
  local dir="$1" warn="$2" strong="$3"
  [ -d "$dir" ] || return 0
  local n
  n=$(find "$dir" -maxdepth 1 -name "*.md" ! -name "MEMORY.md" 2>/dev/null | wc -l | tr -d ' ')
  [ -z "$n" ] && return 0
  if [ "$n" -ge "$strong" ] 2>/dev/null; then
    ISSUES+=("[STRONG] memory/*.md: $n개 / 100개 — /memory-audit 통합·삭제 권장")
    STRONG_HITS+=("memory_files")
  elif [ "$n" -ge "$warn" ] 2>/dev/null; then
    ISSUES+=("[WARN] memory/*.md: $n개 / 60개")
  fi
}

# === 측정 ===
_measure_lines       "TASKS.md"          "$_TASKS_PATH"          "$TASKS_WARN"        "$TASKS_STRONG"
_measure_lines       "HANDOFF.md"        "$_HANDOFF_PATH"        "$HANDOFF_WARN"      "$HANDOFF_STRONG"
_measure_lines       "MEMORY.md"         "$_MEMORY_DIR/MEMORY.md" "$MEMORY_INDEX_WARN" "$MEMORY_INDEX_STRONG"
_measure_memory_files "$_MEMORY_DIR"     "$MEMORY_FILES_WARN"    "$MEMORY_FILES_STRONG"
_measure_bytes       "incident_ledger"   "$_INCIDENT_PATH"       "$INCIDENT_WARN"     "$INCIDENT_STRONG"

# === 출력 + incident 기록 ===
if [ ${#ISSUES[@]} -gt 0 ]; then
  echo "[token_threshold] ⚠️ ${#ISSUES[@]}건 초과:"
  for i in "${ISSUES[@]}"; do
    echo "  $i"
  done
  hook_log "token_threshold" "issues=${#ISSUES[@]} strong=${#STRONG_HITS[@]}"

  # 3회 연속 STRONG 탐지 → incident (hook_log 최근 스캔)
  if [ ${#STRONG_HITS[@]} -gt 0 ] && [ -f "$HOOK_LOG_FILE" ]; then
    local_strong_runs=$(tail -30 "$HOOK_LOG_FILE" 2>/dev/null | grep -c '"event":"token_threshold"[^}]*strong=[1-9]' || echo 0)
    if [ "$local_strong_runs" -ge 3 ] 2>/dev/null; then
      hook_incident "doc_drift" "token_threshold_check" "${STRONG_HITS[*]}" \
        "3회 연속 강경고 — 감축 작업 필요" \
        "\"classification_reason\":\"doc_drift\""
    fi
  fi
fi

hook_timing_end "token_threshold_check" "$_TTC_START" "ok"
exit 0
