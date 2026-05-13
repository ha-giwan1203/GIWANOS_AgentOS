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

# ============================================================================
# delegation guard Phase 0 — 복원 (2026-05-13 세션157 3way 만장일치)
# 합의 매트릭스: GPT 조건부 채택 + Gemini 채택 + Claude 채택 (pass_ratio=1.00)
# 사유: 세션148 폐기 후 13일 만에 사용자 떠넘기기 재발 체감 → 문서 규칙은 필요조건이지 충분조건 아님 실증.
# 형태: 새 hook 추가 없이 본 Stop hook 내부 최소 복원. hook 26개 과밀 회피.
# 로그: 3way 합의 — debate_20260513_211646_3way/round1_cross_verification.md (pass_ratio=1.00)
# ============================================================================

# Stop hook stdin JSON 읽기 — stop_hook_active 검출 (무한 루프 방지)
HOOK_INPUT=$(cat 2>/dev/null || true)
STOP_HOOK_ACTIVE=$(echo "$HOOK_INPUT" | safe_json_get "stop_hook_active" 2>/dev/null || echo "")

# 떠넘기기 패턴 (보수적 — false positive 최소화)
_DELEGATION_PATTERN='(어떻게[[:space:]]*할까요|진행할까요|원하시면[[:space:]]*(말씀|알려|진행)|선택해[[:space:]]*주세요|A/B[[:space:]]*중[[:space:]]*선택|사용자[[:space:]]*결정[[:space:]]*대기|1단어로[[:space:]]*답|확인해주시면[[:space:]]*진행|말씀해주시면[[:space:]]*진행)'
# whitelist — false positive 방지 (토론모드 판정 / 사용자 명시 선택 / ERP·MES 1줄 확인)
_DELEGATION_WHITELIST='(통과[[:space:]]*/[[:space:]]*조건부|조건부[[:space:]]*통과|토론모드|debate-mode|3way|3자[[:space:]]*토론|"물어봐"|"확인해"|"비교해"|"선택지"|ERP/MES|MES[[:space:]]*업로드|MES[[:space:]]*비가역|반영[[:space:]]*대상[[:space:]]*[:：])'

if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
  # 2회차 — 무조건 통과 + incident_ledger 기록 (정규식 과민 추적, GPT 권고)
  _DG_TS=$(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S')
  printf '{"ts":"%s","result":"second_pass","source":"delegation_guard","note":"stop_hook_active=true 2회차 통과"}\n' "$_DG_TS" \
    >> "$PROJECT_ROOT/.claude/logs/delegation_guard.jsonl" 2>/dev/null
  hook_log "Stop" "delegation_guard: stop_hook_active=true 2회차 통과" 2>/dev/null || true
elif [ -n "$LAST_TEXT" ] && echo "$LAST_TEXT" | grep -qiE "$_DELEGATION_PATTERN" && ! echo "$LAST_TEXT" | grep -qiE "$_DELEGATION_WHITELIST"; then
  _DG_MATCH=$(echo "$LAST_TEXT" | grep -oiE "$_DELEGATION_PATTERN" | head -1)
  _DG_SAFE=$(json_escape "$_DG_MATCH" 2>/dev/null || echo "$_DG_MATCH")
  hook_incident "gate_reject" "delegation_guard" "$_DG_MATCH" "위임 떠넘기기 발화 감지 — 패턴 '${_DG_MATCH}'" '"classification_reason":"delegation_pattern","normal_flow":false,"next_action":"판단 1줄+다음행동 1줄로 재작성"' 2>/dev/null || true
  _DG_TS=$(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S')
  printf '{"ts":"%s","result":"block","reason":"delegation_pattern","match":"%s","source":"delegation_guard"}\n' "$_DG_TS" "$_DG_SAFE" \
    >> "$PROJECT_ROOT/.claude/logs/delegation_guard.jsonl" 2>/dev/null
  echo "{\"decision\":\"block\",\"reason\":\"[DELEGATION GUARD] 위임 떠넘기기 패턴 감지: '${_DG_MATCH}'. 질문으로 멈추지 말고 (1) 현재 모드 [A/B/C/D/E] 다시 출력 (2) 네 판단 1줄 (3) 다음 행동 1줄로 재작성하라.\"}"
  hook_timing_end "completion_gate" "$_CMG_START" "block_delegation"
  exit 0
fi

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

# ============================================================================
# verify_receipt gate (Phase 0 — 2026-05-03 세션140)
# 짝 문서: 90_공통기준/업무관리/verify_receipt_gate_plan_20260503.md (v3)
# 3way 합의: GPT PASS / Gemini PASS (SHA b721cb78)
# Phase 0 = no-op: verify_receipts_required.json 모든 SKILL required:false →
#                  skill_required_pattern 빈값 반환 → receipt 검사 건너뜀
# Phase 1+에서 d0-production-plan부터 required:true 승격하면 활성화됨
# ============================================================================
ACTIVE_DIR="$PROJECT_ROOT/.claude/state/active_skills"
REQUIRED_MAP="$PROJECT_ROOT/.claude/state/verify_receipts_required.json"
RECEIPT_DIR="$PROJECT_ROOT/.claude/state/verify_receipts"
if [ -d "$ACTIVE_DIR" ] && [ -s "$REQUIRED_MAP" ]; then
  # 디렉토리 최신 mtime 1건 (Gemini v2 권고: 단일파일 → 개별파일)
  LATEST_ACTIVE=$(ls -t "$ACTIVE_DIR"/*.json 2>/dev/null | head -1)
  if [ -n "$LATEST_ACTIVE" ] && [ -s "$LATEST_ACTIVE" ]; then
    SKILL=$(safe_json_get "skill" < "$LATEST_ACTIVE" 2>/dev/null)
    TASK_ID=$(safe_json_get "task_id" < "$LATEST_ACTIVE" 2>/dev/null)
    STARTED_AT=$(safe_json_get "started_at" < "$LATEST_ACTIVE" 2>/dev/null)
    EXPECTED=$(safe_json_get "expected_receipt" < "$LATEST_ACTIVE" 2>/dev/null)
    REQ=$(skill_required_pattern "$SKILL" "$REQUIRED_MAP" 2>/dev/null)
    # stale marker (24h 초과) → 검사 건너뛰고 hook_log 기록
    NOW_EPOCH=$(date +%s 2>/dev/null || echo 0)
    STARTED_EPOCH=$(iso_to_epoch "$STARTED_AT" 2>/dev/null)
    AGE_SEC=$((NOW_EPOCH - STARTED_EPOCH))
    if [ "$AGE_SEC" -gt 86400 ] 2>/dev/null; then
      hook_log "active_skill_stale" "skill=$SKILL task=$TASK_ID age=${AGE_SEC}s" 2>/dev/null
      REQ=""
    fi
    if [ -n "$REQ" ]; then
      RECEIPT_FAIL=""
      if [ ! -s "$PROJECT_ROOT/$EXPECTED" ]; then
        OVR=$(find_override_receipt "$RECEIPT_DIR/_override" "$SKILL" "$TASK_ID" 2>/dev/null)
        if [ -z "$OVR" ] || ! validate_override "$OVR" 2>/dev/null; then
          RECEIPT_FAIL="missing_receipt_and_no_valid_override"
        else
          hook_log "override_used" "skill=$SKILL task=$TASK_ID file=$OVR" 2>/dev/null
        fi
      else
        R_TASK=$(safe_json_get "task_id" < "$PROJECT_ROOT/$EXPECTED" 2>/dev/null)
        R_RES=$(safe_json_get "result" < "$PROJECT_ROOT/$EXPECTED" 2>/dev/null)
        R_TS=$(safe_json_get "checked_at" < "$PROJECT_ROOT/$EXPECTED" 2>/dev/null)
        R_EPOCH=$(iso_to_epoch "$R_TS" 2>/dev/null)
        [ "$R_TASK" != "$TASK_ID" ] && RECEIPT_FAIL="task_id_mismatch"
        [ "$R_RES" != "PASS" ] && RECEIPT_FAIL="${RECEIPT_FAIL}|result_not_pass"
        [ "$R_EPOCH" -lt "$STARTED_EPOCH" ] 2>/dev/null && RECEIPT_FAIL="${RECEIPT_FAIL}|stale"
      fi
      if [ -n "$RECEIPT_FAIL" ]; then
        # Gemini v2 B 추가제안 채택: error_message에 receipt 규격 + override 사용법 명시
        REASON_TEXT="[COMPLETION GATE] verify_receipt skill=$SKILL task=$TASK_ID fail=$RECEIPT_FAIL\\nrequired: $EXPECTED\\nschema: {task_id=$TASK_ID, skill=$SKILL, result=PASS, checked_at>=$STARTED_AT, external_system|target_files 중 하나 필수}\\noverride: .claude/state/verify_receipts/_override/${SKILL}_*_${TASK_ID}.json (approver+reason>=10자+evidence+expires_at<=24h)"
        printf '{"ts":"%s","result":"block","reason":"verify_receipt_missing","skill":"%s","task":"%s","fail":"%s","source":"gate"}\n' \
          "$(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null)" "$SKILL" "$TASK_ID" "$RECEIPT_FAIL" \
          >> "$PROJECT_ROOT/.claude/logs/completion_claim.jsonl" 2>/dev/null
        echo "{\"decision\":\"block\",\"reason\":\"${REASON_TEXT}\"}"
        hook_timing_end "completion_gate" "$_CMG_START" "block_receipt"
        exit 0
      fi
    fi
  fi
fi

# 정상 통과 경로 기록
_CC_TS=$(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S')
printf '{"ts":"%s","result":"pass","reason":"state_sync_ok","source":"gate"}\n' "$_CC_TS" \
  >> "$PROJECT_ROOT/.claude/logs/completion_claim.jsonl" 2>/dev/null
rm -f "$MARKER" 2>/dev/null

# ============================================================================
# Phase 2-B permissions_sanity 7일 누적 소프트블록 — 제거 (2026-05-08 세션148 토론 합의 3/3)
# 합의 매트릭스: GPT 권고 + Gemini 동의(폐기 기능 잔재) + Claude 채택.
# 사유: permissions_sanity hook 자체는 비활성(98_아카이브/_deprecated_v1/hooks/).
#   completion_gate가 산출물 로그(hook_log.jsonl의 "permissions_sanity ... 경고")만
#   7일 누적 검사하던 잔존 의존. 죽은 hook의 그림자.
# 기존 .claude/state/completion_gate_phase2b_last.txt cache는 그대로 둠 (참조 안 함).
# ============================================================================

hook_timing_end "completion_gate" "$_CMG_START" "pass"
exit 0
