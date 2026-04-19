#!/bin/bash
# doctor_lite — session_start 경량 진단 (3~5초 내)
# 목적: settings/hook/필수 파일 드리프트 조기 탐지. 풀 진단은 수동 `claude doctor`.
# 2026-04-18 3자 토론 합의안 4번 (우선순위 3, GPT+Gemini 동의)

source "$(dirname "$0")/hook_common.sh"

ISSUES=()

# 1. settings JSON 문법 검증 — team+local 양쪽 (세션74)
for SETTINGS_FILE in \
    "$PROJECT_ROOT/.claude/settings.json" \
    "$PROJECT_ROOT/.claude/settings.local.json"; do
  if [ -f "$SETTINGS_FILE" ]; then
    if ! python3 -c "import json,sys; json.load(open(sys.argv[1], encoding='utf-8'))" "$SETTINGS_FILE" 2>/dev/null; then
      ISSUES+=("$(basename "$SETTINGS_FILE") JSON 문법 오류")
    fi
  fi
done

# 2. 필수 hook 파일 존재 체크
REQ_HOOKS=(
  "session_start_restore.sh"
  "completion_gate.sh"
  "final_check.sh"
  "hook_common.sh"
)
for h in "${REQ_HOOKS[@]}"; do
  if [ ! -f "$PROJECT_ROOT/.claude/hooks/$h" ]; then
    ISSUES+=("필수 hook 누락: $h")
  fi
done

# 3. 핵심 문서 접근
REQ_DOCS=(
  "CLAUDE.md"
  "90_공통기준/업무관리/TASKS.md"
  "90_공통기준/업무관리/HANDOFF.md"
)
for d in "${REQ_DOCS[@]}"; do
  if [ ! -f "$PROJECT_ROOT/$d" ]; then
    ISSUES+=("필수 문서 누락: $d")
  fi
done

# 4. Git 저장소 상태
if ! git -C "$PROJECT_ROOT" rev-parse --git-dir > /dev/null 2>&1; then
  ISSUES+=("git 저장소 아님")
fi

# 결과 출력
if [ ${#ISSUES[@]} -eq 0 ]; then
  echo "[doctor_lite] OK"
else
  echo "[doctor_lite] ⚠️ ${#ISSUES[@]}건:"
  for i in "${ISSUES[@]}"; do
    echo "  - $i"
  done
  hook_log "doctor_lite" "issues=${#ISSUES[@]}"
fi

exit 0
