#!/bin/bash
# SessionStart hook: startup/resume/compact 시 session_kernel.md 재주입
# 주의: stdout 주입은 버그 가능성 있음 (이슈 #13912, #17550)
# → 파일에 출력 후 경로 안내 방식으로 동작

source "$(dirname "$0")/hook_common.sh"
# 훅 등급: measurement (Phase 2-C 2026-04-19 세션73 timing 배선)
_SSR_START=$(hook_timing_start)

INPUT=$(cat)
SOURCE=$(printf '%s' "$INPUT" | safe_json_get "source" 2>/dev/null || echo "unknown")
KERNEL_FILE="$PROJECT_ROOT/.claude/state/session_kernel.md"

# evidence 세션 경계 갱신: 새 세션 시작 시 START_FILE 타임스탬프 강제 갱신
# 이전 세션의 .req가 잔존해도 START_FILE이 더 새로우면 evidence_gate가 무시함
SK=$(session_key)
EV_START="$STATE_EVIDENCE/$SK/.session_start"
if [ -d "$STATE_EVIDENCE/$SK" ]; then
  touch "$EV_START"
  hook_log "session_start_restore" "evidence START_FILE refreshed sk=$SK"
fi

# instruction_reads 세션 초기화: 이전 세션의 읽기 마커 무효화
INSTRUCTION_DIR="$PROJECT_ROOT/.claude/state/instruction_reads"
if [ -d "$INSTRUCTION_DIR" ]; then
  rm -f "$INSTRUCTION_DIR"/*.ok 2>/dev/null
  hook_log "session_start_restore" "instruction_reads cleared"
fi

# 스킬 진입 세션캐시 무효화 (D안 2026-04-20): 이전 세션 탭/채팅방 재사용 금지.
# 1회차는 전체 진입, 2회차 이후만 1-B 스킵. 존재 여부로 판정.
STATE_DIR="$PROJECT_ROOT/.claude/state"
rm -f "$STATE_DIR/gpt_skill_entry.ok" "$STATE_DIR/gemini_skill_entry.ok" 2>/dev/null
hook_log "session_start_restore" "skill_entry markers cleared"

# Self-X Layer 1 health_summary_first marker 제거됨 (Plan stage1-I5 2026-04-22).
# health_summary_gate 폐기에 따라 해당 marker 의존 로직도 삭제.

hook_log "session_start_restore" "source=$SOURCE"

# hook_config.json에서 설정 읽기 (Phase 2: 중앙 설정형)
CONFIG_FILE="$PROJECT_ROOT/.claude/hook_config.json"
STALE_HOURS=24
FALLBACK_TASKS_LINES=20
FALLBACK_HANDOFF_LINES=20
if [ -f "$CONFIG_FILE" ]; then
  _h=$(grep '"kernel_stale_threshold_hours"' "$CONFIG_FILE" 2>/dev/null | sed 's/[^0-9]//g' | head -1)
  [ -n "$_h" ] && STALE_HOURS="$_h"
  _t=$(grep '"fallback_tasks_lines"' "$CONFIG_FILE" 2>/dev/null | sed 's/[^0-9]//g' | head -1)
  [ -n "$_t" ] && FALLBACK_TASKS_LINES="$_t"
  _hf=$(grep '"fallback_handoff_lines"' "$CONFIG_FILE" 2>/dev/null | sed 's/[^0-9]//g' | head -1)
  [ -n "$_hf" ] && FALLBACK_HANDOFF_LINES="$_hf"
fi
STALE_SECONDS=$(( STALE_HOURS * 3600 ))

# kernel 상태 판정: fresh / stale / missing
KERNEL_STATE="missing"
if [ -f "$KERNEL_FILE" ]; then
  KERNEL_MTIME=$(file_mtime "$KERNEL_FILE")
  NOW=$(date +%s)
  AGE=$(( NOW - KERNEL_MTIME ))
  AGE_H=$(( AGE / 3600 ))
  if [ "$AGE" -gt "$STALE_SECONDS" ]; then
    KERNEL_STATE="stale"
  else
    KERNEL_STATE="fresh"
  fi
fi

# kernel fresh → 기존 로직 (kernel 내용 출력)
if [ "$KERNEL_STATE" = "fresh" ]; then
  echo "=== [session_start: $SOURCE] 이전 세션 상태 ==="

  # Getting Bearings: pwd + git log (Anthropic 패턴, Phase 3-3)
  echo "--- 현재 위치: $(pwd) ---"
  echo "--- 최근 커밋 5건 ---"
  git log --oneline -5 2>/dev/null || echo "(git log 실패)"

  # TASKS 상단 (원본 문서 우선)
  echo "--- TASKS 상단 ---"
  head -"$FALLBACK_TASKS_LINES" "$PATH_TASKS" 2>/dev/null
  # HANDOFF 최신 세션
  echo "--- HANDOFF 최신 세션 ---"
  head -"$FALLBACK_HANDOFF_LINES" "$PATH_HANDOFF" 2>/dev/null

  # progress.json 캐시 (참고용, 원본 문서 뒤에 출력)
  PROGRESS_FILE="$PROJECT_ROOT/.claude/state/session_progress.json"
  if [ -f "$PROGRESS_FILE" ]; then
    CURRENT_TASK=$(grep '"current_task"' "$PROGRESS_FILE" 2>/dev/null | sed 's/.*: *"\(.*\)".*/\1/' | head -1)
    if [ -n "$CURRENT_TASK" ] && [ "$CURRENT_TASK" != "" ]; then
      echo "--- 이전 작업 (캐시, 참고용) ---"
      echo "진행 중: $CURRENT_TASK"
    fi
  fi

  echo "=== session_kernel 끝 ==="
  hook_log "session_start_restore" "kernel fresh — 출력 완료 source=$SOURCE age=${AGE}s"

# kernel stale/missing → fallback: TASKS + HANDOFF 직접 읽기 (Phase 2 개선)
else
  if [ "$KERNEL_STATE" = "stale" ]; then
    echo "[session_start] ⚠️ session_kernel.md가 ${AGE_H}시간 전 저장 — stale. 원본 문서 fallback 사용."
  else
    echo "[session_start] session_kernel.md 없음 — 원본 문서 fallback 사용."
  fi

  echo "=== [session_start: $SOURCE] fallback — 원본 문서 직접 읽기 ==="

  # Getting Bearings: pwd + git log (Anthropic 패턴, Phase 3-3)
  echo "--- 현재 위치: $(pwd) ---"
  echo "--- 최근 커밋 5건 ---"
  git log --oneline -5 2>/dev/null || echo "(git log 실패)"

  # TASKS 상단 (복구 우선순위 1위)
  echo "--- TASKS 상단 (${FALLBACK_TASKS_LINES}줄) ---"
  head -"$FALLBACK_TASKS_LINES" "$PATH_TASKS" 2>/dev/null || echo "(TASKS.md 없음)"

  # HANDOFF 최신 세션 (복구 우선순위 2위)
  echo "--- HANDOFF 최신 세션 (${FALLBACK_HANDOFF_LINES}줄) ---"
  head -"$FALLBACK_HANDOFF_LINES" "$PATH_HANDOFF" 2>/dev/null || echo "(HANDOFF.md 없음)"

  # 활성 도메인 (있으면 1줄)
  DOMAIN_REQ="$PROJECT_ROOT/.claude/state/active_domain.req"
  if [ -f "$DOMAIN_REQ" ]; then
    echo "--- 활성 도메인: $(cat "$DOMAIN_REQ") ---"
  fi

  # progress.json 캐시 (참고용, 맨 뒤)
  PROGRESS_FILE="$PROJECT_ROOT/.claude/state/session_progress.json"
  if [ -f "$PROGRESS_FILE" ]; then
    CURRENT_TASK=$(grep '"current_task"' "$PROGRESS_FILE" 2>/dev/null | sed 's/.*: *"\(.*\)".*/\1/' | head -1)
    if [ -n "$CURRENT_TASK" ] && [ "$CURRENT_TASK" != "" ]; then
      echo "--- 이전 작업 (캐시, 참고용) ---"
      echo "진행 중: $CURRENT_TASK"
    fi
  fi

  echo "=== fallback 끝 ==="
  hook_log "session_start_restore" "kernel $KERNEL_STATE — fallback 출력 source=$SOURCE"
fi

hook_log "session_start_restore" "kernel 출력 완료 source=$SOURCE age=${AGE}s"

# folder_map: 신규 파일 화이트리스트 (write_router_gate.sh 정책 — plan polymorphic-prancing-allen)
# 모델이 세션 시작 시 폴더 정책을 컨텍스트로 갖게 해 위반 자체를 줄인다 (재발 방지의 절반).
echo "[folder_map] 신규 파일 화이트리스트:"
echo "  실무: 01_인사근태 / 02_급여단가 / 03_품번관리 / 04_생산계획 / 05_생산실적 / 06_생산관리 / 07_라인정지비용 / 08_공정개선이슈 / 09_외주발주납품 / 10_라인배치"
echo "  공통: 90_공통기준 / 98_아카이브 / 99_임시수집(default) / .claude"
echo "  임시·검토 파일은 99_임시수집/ 강제. 워크트리 루트에 새 파일 금지(CLAUDE.md/README.md/.gitignore 외)."

# Fast smoke subset — 로컬·결정적 검증만 (차단 아님, 경고만)
FAST_SMOKE="$(dirname "$0")/smoke_fast.sh"
if [ -x "$FAST_SMOKE" ]; then
  FAST_RESULT=$("$FAST_SMOKE" 2>&1)
  echo "$FAST_RESULT"
  hook_log "session_start_restore" "fast_smoke: $FAST_RESULT"
fi

# doctor_lite — 경량 설정 드리프트 진단 (3자 토론 2026-04-18 합의)
DOCTOR_LITE="$(dirname "$0")/doctor_lite.sh"
if [ -x "$DOCTOR_LITE" ]; then
  DOCTOR_RESULT=$("$DOCTOR_LITE" 2>&1)
  echo "$DOCTOR_RESULT"
fi

# token_threshold_check — 저장소 문서 비대화 감시 (세션68 3자 합의 / 세션79 실물 구현)
TOKEN_CHK="$(dirname "$0")/token_threshold_check.sh"
if [ -x "$TOKEN_CHK" ]; then
  TOKEN_RESULT=$("$TOKEN_CHK" 2>&1)
  [ -n "$TOKEN_RESULT" ] && echo "$TOKEN_RESULT"
fi

# domain_status_sync — 도메인 STATUS.md drift advisory (세션98 2자 토론 C2 합의)
DOMAIN_SYNC="$(dirname "$0")/domain_status_sync.sh"
if [ -x "$DOMAIN_SYNC" ]; then
  DOMAIN_RESULT=$("$DOMAIN_SYNC" 2>&1)
  [ -n "$DOMAIN_RESULT" ] && echo "$DOMAIN_RESULT"
fi

# 드리프트 경고: TASKS/HANDOFF/STATUS 상단 날짜 비교 (hook_config.json drift_check 연동)
DRIFT_PATTERN="최종 업데이트"
if [ -f "$CONFIG_FILE" ]; then
  _dp=$(grep '"date_pattern"' "$CONFIG_FILE" 2>/dev/null | sed 's/.*: *"\(.*\)".*/\1/' | head -1)
  [ -n "$_dp" ] && DRIFT_PATTERN="$_dp"
fi
_extract_date() {
  sed -n "s/.*${DRIFT_PATTERN}: \([0-9-]*\).*/\1/p" "$1" 2>/dev/null | head -1
}
_TASKS_DATE=$(_extract_date "$PATH_TASKS")
_HANDOFF_DATE=$(_extract_date "$PATH_HANDOFF")
_STATUS_DATE=$(_extract_date "$PROJECT_ROOT/90_공통기준/업무관리/STATUS.md")
if [ -n "$_TASKS_DATE" ] && [ -n "$_HANDOFF_DATE" ] && [ -n "$_STATUS_DATE" ]; then
  if [ "$_TASKS_DATE" != "$_HANDOFF_DATE" ] || [ "$_TASKS_DATE" != "$_STATUS_DATE" ]; then
    echo "[DRIFT] 상태 문서 날짜 불일치: TASKS=$_TASKS_DATE / HANDOFF=$_HANDOFF_DATE / STATUS=$_STATUS_DATE"
    hook_log "session_start_restore" "DRIFT detected: T=$_TASKS_DATE H=$_HANDOFF_DATE S=$_STATUS_DATE"
  fi
fi

# Plan glimmering-churning-reef Part 4-B: last_selfcheck freshness 표시 (정보만, 자동 조치 없음)
LAST_SELFCHECK="$PROJECT_ROOT/.claude/self/last_selfcheck.txt"
if [ -f "$LAST_SELFCHECK" ]; then
  _LS_MTIME=$(file_mtime "$LAST_SELFCHECK")
  _LS_NOW=$(date +%s)
  _LS_AGE_D=$(( ( _LS_NOW - _LS_MTIME ) / 86400 ))
  if [ "$_LS_AGE_D" -ge 14 ]; then
    echo "--- selfcheck ${_LS_AGE_D}일 전 실행 (14일 초과 — 수동 bash .claude/self/selfcheck.sh 권장) ---"
  elif [ "$_LS_AGE_D" -ge 7 ]; then
    echo "--- selfcheck ${_LS_AGE_D}일 전 실행 (7일 초과) ---"
  else
    echo "--- selfcheck ${_LS_AGE_D}일 전 실행 ---"
  fi
else
  echo "--- selfcheck 미실행 (bash .claude/self/selfcheck.sh 권장) ---"
fi

# Phase 3-1: 미해결 incident 요약 + 24h 신규 건수
INCIDENT_LEDGER="$PROJECT_ROOT/.claude/incident_ledger.jsonl"
if [ -f "$INCIDENT_LEDGER" ]; then
  TOTAL_COUNT=$(wc -l < "$INCIDENT_LEDGER" 2>/dev/null | tr -d ' ')
  RESOLVED_COUNT=$(grep -c '"resolved":true\|"resolved": true' "$INCIDENT_LEDGER" 2>/dev/null || echo 0)
  OPEN_COUNT=$(( TOTAL_COUNT - RESOLVED_COUNT ))
  # 24시간 이내 신규 건수 (incident 필드명: "ts")
  # 세션86: ledger ts는 UTC(Z 접미사) → cutoff도 UTC로 생성 (-u). KST 로컬 시간으로 비교 시 9시간 오프셋 발생
  CUTOFF_24H=$(date -u -d "-24 hours" "+%Y-%m-%dT%H:%M" 2>/dev/null || date -u -v-24H "+%Y-%m-%dT%H:%M" 2>/dev/null || echo "")
  RECENT_COUNT=0
  if [ -n "$CUTOFF_24H" ]; then
    RECENT_COUNT=$(awk -v cutoff="$CUTOFF_24H" '/"ts"/ { match($0, /"ts":"([^"]+)"/, a); if(a[1] >= cutoff) c++ } END { print c+0 }' "$INCIDENT_LEDGER" 2>/dev/null || echo 0)
  fi
  if [ "$OPEN_COUNT" -gt 0 ] || [ "$RECENT_COUNT" -gt 0 ]; then
    echo "--- 미해결 incident: ${OPEN_COUNT}건 (총 ${TOTAL_COUNT}건, 최근24h 신규 ${RECENT_COUNT}건) ---"
    echo "    /auto-fix 로 분석 가능"
  fi
fi

hook_timing_end "session_start_restore" "$_SSR_START" "$KERNEL_STATE"
exit 0
