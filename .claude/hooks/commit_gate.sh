#!/bin/bash
# commit_gate.sh — git commit/push 전 자체검증 강제 (PreToolUse/Bash)
# final_check.sh --fast 실패 시 커밋/푸시 차단
# hook 변경 감지 시 --full 자동 승격
# GPT+Claude 합의 2026-04-07

source "$(dirname "$0")/hook_common.sh" 2>/dev/null || true

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
    exit 0
  fi
fi
# git commit 또는 git push가 아니면 통과
if ! echo "$COMMAND" | grep -qE 'git (commit|push)'; then
  exit 0
fi

hook_log "PreToolUse/Bash" "commit_gate: git commit/push 감지" 2>/dev/null

# Circuit breaker: 동일 hook에서 연속 3건 이상 unresolved → 경고
if circuit_breaker_tripped "commit_gate" 3 2>/dev/null; then
  hook_log "PreToolUse/Bash" "commit_gate: ⚠ circuit breaker — 연속 3회 이상 unresolved incident. 이전 실패 원인 해결 후 커밋 권장"
  echo "⚠ [CIRCUIT BREAKER] commit_gate 연속 3회+ unresolved incident 감지. 이전 실패 원인(.claude/incident_ledger.jsonl)을 먼저 확인하세요."
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
HOOKS_DIR="$PROJECT_DIR/.claude/hooks"

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

  # fingerprint 기반 incident suppress (GPT+Claude 합의 세션44):
  # evidence_gate 동일 패턴. 차단(deny)은 유지, incident 기록만 grace window 내 중복 생략
  local GRACE_WINDOW=60
  local _fp_raw
  _fp_raw="${MODE:0:20}|${NORMAL_FLOW}|${FAIL_KEYWORDS:0:80}"
  local _fingerprint
  if command -v sha1sum >/dev/null 2>&1; then
    _fingerprint=$(printf '%s' "$_fp_raw" | sha1sum | cut -c1-16)
  elif command -v md5sum >/dev/null 2>&1; then
    _fingerprint=$(printf '%s' "$_fp_raw" | md5sum | cut -c1-16)
  else
    _fingerprint=$(printf '%s' "$_fp_raw" | cksum | awk '{print $1}' | cut -c1-16)
  fi

  local _should_record=true
  INCIDENT_LEDGER="${INCIDENT_LEDGER:-$PROJECT_DIR/.claude/incident_ledger.jsonl}"
  if [ -f "$INCIDENT_LEDGER" ]; then
    local _now _cutoff
    _now=$(date +%s 2>/dev/null || echo 0)
    _cutoff=$((_now - GRACE_WINDOW))
    while IFS= read -r _line; do
      local _fp_in_line _ts_in_line _epoch
      _fp_in_line=$(printf '%s' "$_line" | safe_json_get "fingerprint" 2>/dev/null)
      if [ "$_fp_in_line" = "$_fingerprint" ]; then
        _ts_in_line=$(printf '%s' "$_line" | safe_json_get "ts" 2>/dev/null)
        _epoch=$(date -d "$_ts_in_line" +%s 2>/dev/null || \
                 date -jf "%Y-%m-%dT%H:%M:%SZ" "$_ts_in_line" +%s 2>/dev/null || echo 0)
        if [ "$_epoch" -gt "$_cutoff" ] 2>/dev/null; then
          _should_record=false
          break
        fi
      fi
    done < <(tail -30 "$INCIDENT_LEDGER")
  fi

  if [ "$_should_record" = "true" ]; then
    hook_incident "gate_reject" "commit_gate" "" "final_check $MODE FAIL" "\"classification_reason\":\"pre_commit_check\",\"mode\":\"$MODE\",\"promoted_to_full\":$PROMOTED,\"normal_flow\":$NORMAL_FLOW,\"fail_keywords\":\"$FAIL_KEYWORDS\",\"warn_keywords\":\"$WARN_KEYWORDS\",\"fingerprint\":\"$_fingerprint\",\"next_action\":\"./.claude/hooks/final_check.sh $MODE 를 다시 실행해 FAIL 항목부터 정리\"" 2>/dev/null || true
  else
    hook_log "PreToolUse/Bash" "commit_gate: incident suppress (fingerprint=$_fingerprint, grace=${GRACE_WINDOW}s)" 2>/dev/null
  fi
  echo "{\"decision\":\"deny\",\"reason\":\"[COMMIT GATE] final_check $MODE 실패 — 자체검증 통과 후 커밋하세요.\\n$FAILS\"}"
  exit 0
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
exit 0
