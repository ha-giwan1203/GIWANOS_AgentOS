#!/bin/bash
# commit_gate.sh — git commit/push 전 자체검증 강제 (PreToolUse/Bash)
# final_check.sh --fast 실패 시 커밋/푸시 차단
# hook 변경 감지 시 --full 자동 승격
# GPT+Claude 합의 2026-04-07
#
# 훅 등급: gate (의제5 Phase 2-B 전환 2026-04-19 세션72)
#   - 차단 메커니즘: JSON `{"hookSpecificOutput":{"permissionDecision":"deny",...}}` (PreToolUse 최신 스펙) + exit 2 (belt-and-suspenders)
#   - timing 계측: hook_timing_start/end 호출부 배선 완료

source "$(dirname "$0")/hook_common.sh" 2>/dev/null || true

# Phase 2-B: 전체 실행 시간 계측 (의제4 수집 데이터)
_CG_START=$(hook_timing_start)

# --- fingerprint suppress 함수 (세션46 GPT+Claude 합의: 2단 분리) ---

# build_fingerprint: 모드+흐름+키워드로 16자 해시 생성
# Usage: fp=$(build_fingerprint "$MODE" "$NORMAL_FLOW" "$FAIL_KEYWORDS")
build_fingerprint() {
  local mode="$1" normal_flow="$2" fail_kw="$3"
  local raw="${mode:0:20}|${normal_flow}|${fail_kw:0:80}"
  if command -v sha1sum >/dev/null 2>&1; then
    printf '%s' "$raw" | sha1sum | cut -c1-16
  elif command -v md5sum >/dev/null 2>&1; then
    printf '%s' "$raw" | md5sum | cut -c1-16
  else
    printf '%s' "$raw" | cksum | awk '{print $1}' | cut -c1-16
  fi
}

# should_suppress_incident: grace window 내 동일 fingerprint 중복이면 true(0)
# Usage: if should_suppress_incident "$fingerprint" 60; then ...suppress...
should_suppress_incident() {
  local fingerprint="$1" grace_window="${2:-60}"
  local ledger="${INCIDENT_LEDGER:-${PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}/.claude/incident_ledger.jsonl}"
  [ -f "$ledger" ] || return 1
  local now cutoff
  now=$(date +%s 2>/dev/null || echo 0)
  cutoff=$((now - grace_window))
  local line fp_in ts_in epoch
  while IFS= read -r line; do
    fp_in=$(printf '%s' "$line" | safe_json_get "fingerprint" 2>/dev/null)
    if [ "$fp_in" = "$fingerprint" ]; then
      ts_in=$(printf '%s' "$line" | safe_json_get "ts" 2>/dev/null)
      epoch=$(date -d "$ts_in" +%s 2>/dev/null || \
              date -jf "%Y-%m-%dT%H:%M:%SZ" "$ts_in" +%s 2>/dev/null || echo 0)
      if [ "$epoch" -gt "$cutoff" ] 2>/dev/null; then
        return 0  # suppress
      fi
    fi
  done < <(tail -30 "$ledger")
  return 1  # no suppress — should record
}

INPUT=$(cat)
# 안전 JSON 파서 사용 (sed 단독 파싱 취약성 대체, GPT+Claude 합의 2026-04-07)
COMMAND=$(echo "$INPUT" | safe_json_get "command")

# fail-closed 보강 (GPT+Claude 합의 2026-04-11):
# safe_json_get 파싱 실패 시 COMMAND=""이 되어 게이트가 무력화되던 문제 수정.
# COMMAND가 비어도 raw INPUT에 git commit/push가 있으면 파싱 실패로 간주하여 fallback 검사.
if [ -z "$COMMAND" ]; then
  # 파싱 실패 fallback: raw INPUT에서 직접 확인
  if echo "$INPUT" | grep -qE 'git (commit|push)'; then
    hook_log "PreToolUse/Bash" "commit_gate: JSON 파싱 실패 fallback — raw INPUT에서 git commit/push 감지" 2>/dev/null
    COMMAND="git commit"  # fallback 값 설정하여 아래 검사 계속 진행
  else
    hook_timing_end "commit_gate" "$_CG_START" "skip_empty"
    exit 0
  fi
fi
# git commit 또는 git push가 아니면 통과
if ! echo "$COMMAND" | grep -qE 'git (commit|push)'; then
  hook_timing_end "commit_gate" "$_CG_START" "skip_nongit"
  exit 0
fi

hook_log "PreToolUse/Bash" "commit_gate: git commit/push 감지" 2>/dev/null

# 세션91 2자 토론 단계 III-1 (2026-04-22): write_marker 동봉 강제 블록 제거.
# 원칙 5 "commit_gate = Git/staging만". 상태문서 갱신 검증은 completion_gate 단일 소유.
# 제거 전 로직은 90_공통기준/토론모드/logs/debate_20260422_stage3_2way/SUMMARY.md 커밋 A 섹션 참조.

# Circuit breaker: 동일 hook에서 연속 3건 이상 unresolved → 경고
# 세션124: 사용자 가시 echo 제거 — Claude Code PreToolUse hook이 stdout/stderr 출력을 block 응답으로 오인하는 문제 해결.
# hook_log 기록은 유지 (필요 시 .claude/hooks/hook_log.jsonl 또는 /현재상태 슬래시 명령어로 확인 가능).
if circuit_breaker_tripped "commit_gate" 3 2>/dev/null; then
  hook_log "PreToolUse/Bash" "commit_gate: ⚠ circuit breaker — 연속 3회 이상 unresolved incident. 이전 실패 원인 해결 후 커밋 권장"
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
HOOKS_DIR="$PROJECT_DIR/.claude/hooks"

# git push 단독은 final_check 스킵 (세션76 근본 해결):
# push는 이미 commit 완료된 상태의 원격 동기화. commit 단계에서 final_check 통과한 내용을 push에서 재검사하는 것은
# Policy-Workflow Mismatch(세션75 3자 토론 Round 1 채택 의제)의 전형 — write_marker 상태가 commit 후에도 유지되어
# 정상 push도 "TASKS/HANDOFF 미갱신" FAIL로 차단되는 문제 발생. commit 단계 검사만으로 통제 목적 충분하므로 중복 제거.
if echo "$COMMAND" | grep -q 'git push' && ! echo "$COMMAND" | grep -q 'git commit'; then
  hook_log "PreToolUse/Bash" "commit_gate PASS: git push 단독 — final_check 스킵 (commit 단계에서 이미 검증)" 2>/dev/null
  hook_timing_end "commit_gate" "$_CG_START" "skip_push_only"
  exit 0
fi

# hook/settings 변경이 포함된 커밋인지 확인 → --full 승격
MODE="--fast"
STAGED=$(cd "$PROJECT_DIR" && git diff --cached --name-only 2>/dev/null)
if echo "$STAGED" | grep -qE '(\.claude/hooks/|settings.*\.json)'; then
  MODE="--full"
fi

# final_check 실행
RESULT=$(bash "$HOOKS_DIR/final_check.sh" "$MODE" 2>&1)
EXIT_CODE=$?

if [ "$EXIT_CODE" -ne 0 ]; then
  # FAIL 항목만 추출하여 간결한 메시지
  FAILS=$(echo "$RESULT" | grep -E '\[FAIL\]|\[WARN\]' | head -5)
  # 승격 여부 판정
  PROMOTED="false"
  if [ "$MODE" = "--full" ]; then
    PROMOTED="true"
  fi
  # FAIL/WARN 상위 키워드 추출 (최대 3개)
  FAIL_KEYWORDS=$(echo "$RESULT" | grep -oE '\[FAIL\] [^|]+' | head -3 | tr '\n' '; ' | sed 's/; $//')
  WARN_KEYWORDS=$(echo "$RESULT" | grep -oE '\[WARN\] [^|]+' | head -3 | tr '\n' '; ' | sed 's/; $//')
  # Normal flow 판정: FAIL이 TASKS/HANDOFF 관련만이면 정상 안전장치 발화
  NORMAL_FLOW="false"
  if echo "$FAIL_KEYWORDS" | grep -qiE 'TASKS|HANDOFF'; then
    OTHER_FAILS=$(echo "$RESULT" | grep -E '\[FAIL\]' | grep -viE 'TASKS|HANDOFF' | head -1)
    if [ -z "$OTHER_FAILS" ]; then
      NORMAL_FLOW="true"
    fi
  fi
  hook_log "PreToolUse/Bash" "commit_gate BLOCK: final_check $MODE FAIL | promoted=$PROMOTED | normal_flow=$NORMAL_FLOW | fails=$FAIL_KEYWORDS | warns=$WARN_KEYWORDS" 2>/dev/null

  # fingerprint 기반 incident suppress (GPT+Claude 합의 세션44, 세션46 2단 함수화):
  # 세션93 (2026-04-22 auto-fix A-3): GRACE_WINDOW 60 → 300
  #   실측 근거: incident_ledger fp 상위 8개가 commit_gate pre_commit_check.
  #   동일 fp `cd129792fc8e4770` 15회 반복, `ae1d9d6036d129b8` 6회 등. 반복 간격 대부분 60초 초과.
  #   evidence_gate와 동일한 GRACE 300 적용 (세션86 합의). 차단은 유지, 기록 중복만 억제.
  _GRACE_WINDOW=300
  _fingerprint=$(build_fingerprint "$MODE" "$NORMAL_FLOW" "$FAIL_KEYWORDS")
  if should_suppress_incident "$_fingerprint" "$_GRACE_WINDOW"; then
    hook_log "PreToolUse/Bash" "commit_gate: incident suppress (fingerprint=$_fingerprint, grace=${_GRACE_WINDOW}s)" 2>/dev/null
  else
    hook_incident "gate_reject" "commit_gate" "" "final_check $MODE FAIL" "\"classification_reason\":\"pre_commit_check\",\"mode\":\"$MODE\",\"promoted_to_full\":$PROMOTED,\"normal_flow\":$NORMAL_FLOW,\"fail_keywords\":\"$FAIL_KEYWORDS\",\"warn_keywords\":\"$WARN_KEYWORDS\",\"fingerprint\":\"$_fingerprint\",\"next_action\":\"./.claude/hooks/final_check.sh $MODE 를 다시 실행해 FAIL 항목부터 정리\"" 2>/dev/null || true
  fi
  echo "{\"hookSpecificOutput\":{\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"[COMMIT GATE] final_check $MODE 실패 — 자체검증 통과 후 커밋하세요.\\n$FAILS\"}}"
  hook_timing_end "commit_gate" "$_CG_START" "block_final_check"
  exit 2
fi

# === C2: WARN 개별 incident 기록 (세션45 학습 루프 사각지대 해소) ===
# 커밋 성공(PASS)이어도 WARN이 있으면 학습 루프에 기록 (normal_flow=true)
# PASS 경로에서는 WARN_KEYWORDS가 미정의이므로 여기서 추출
if [ -z "${WARN_KEYWORDS+x}" ]; then
  WARN_KEYWORDS=$(echo "$RESULT" | grep -oE '\[WARN\] [^|]+' | head -3 | tr '\n' '; ' | sed 's/; $//')
fi
if [ -n "$WARN_KEYWORDS" ]; then
  if echo "$WARN_KEYWORDS" | grep -qi '드리프트'; then
    hook_incident "warn_recorded" "commit_gate" "" "문서 드리프트 감지" \
      "\"classification_reason\":\"doc_drift\",\"source\":\"final_check\",\"warn_raw\":\"$WARN_KEYWORDS\",\"normal_flow\":true" 2>/dev/null || true
  fi
  if echo "$WARN_KEYWORDS" | grep -qi 'python3'; then
    hook_incident "warn_recorded" "commit_gate" "" "python3 의존 잔존" \
      "\"classification_reason\":\"python3_dependency\",\"source\":\"final_check\",\"warn_raw\":\"$WARN_KEYWORDS\",\"normal_flow\":true" 2>/dev/null || true
  fi
fi

hook_log "PreToolUse/Bash" "commit_gate PASS: final_check $MODE" 2>/dev/null
hook_timing_end "commit_gate" "$_CG_START" "pass"
exit 0
