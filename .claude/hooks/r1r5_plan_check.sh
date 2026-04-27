#!/bin/bash
# r1r5_plan_check.sh — C 트리거 staged 시 R1~R5 plan 흔적 권장 (advisory)
# 별건 2번 (세션118 신설). Gemini Round 2 제안 흡수.
# 훅 등급: advisory. 차단 안 함, stderr 경고 + hook_log + exit 0
# 합의: 90_공통기준/토론모드/logs/debate_20260427_185903_3way/ Round 2 + 본 plan

source "$(dirname "$0")/hook_common.sh" 2>/dev/null || true

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | safe_json_get "command")

# git commit 미감지 → skip
if ! echo "${COMMAND:-$INPUT}" | grep -qE 'git (commit)'; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$PROJECT_DIR" 2>/dev/null || exit 0

# C 강제 승격 트리거 7개 경로 (루트 CLAUDE.md "C 강제 승격 트리거")
STAGED=$(git diff --cached --name-only 2>/dev/null)
[ -z "$STAGED" ] && exit 0

# C 트리거 매칭
TRIGGER_HITS=$(echo "$STAGED" | grep -E '^\.claude/(hooks|settings.*\.json|commands|agents)/|^90_공통기준/스킬/.+/SKILL\.md$|^CLAUDE\.md$|/CLAUDE\.md$' || true)

if [ -z "$TRIGGER_HITS" ]; then
  exit 0
fi

# plan 흔적 검사
# 1) staged 파일에 .claude/plans/ 경로 포함 OR
# 2) staged markdown 파일 본문에 R1, R2, R3, R4, R5 키워드 5개 모두 포함 OR
# 3) 커밋 메시지(.git/COMMIT_EDITMSG 또는 -m 인자)에 R1~R5 또는 plan 언급
HAS_PLAN_REF=0

if echo "$STAGED" | grep -q '\.claude/plans/'; then
  HAS_PLAN_REF=1
fi

if [ "$HAS_PLAN_REF" = "0" ]; then
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    case "$f" in
      *.md)
        if [ -f "$f" ]; then
          if grep -qE '\bR1\b' "$f" 2>/dev/null && \
             grep -qE '\bR2\b' "$f" 2>/dev/null && \
             grep -qE '\bR3\b' "$f" 2>/dev/null && \
             grep -qE '\bR4\b' "$f" 2>/dev/null && \
             grep -qE '\bR5\b' "$f" 2>/dev/null; then
            HAS_PLAN_REF=1
            break
          fi
        fi
        ;;
    esac
  done <<< "$STAGED"
fi

if [ "$HAS_PLAN_REF" = "0" ]; then
  # -m 인자 추출 시도 (간이): COMMAND에 -m 뒤 문자열에 plan 또는 R1~R5 포함?
  if echo "$COMMAND" | grep -qiE '(R1.*R5|plan-first|\.claude/plans/)'; then
    HAS_PLAN_REF=1
  fi
fi

if [ "$HAS_PLAN_REF" = "0" ]; then
  TRIGGER_LINES=$(echo "$TRIGGER_HITS" | head -3 | paste -sd';' -)
  echo "⚠ [r1r5_plan_check] C 트리거 staged인데 R1~R5 plan 흔적 없음 — plan 권장 후 진행" >&2
  echo "  staged C 트리거: $TRIGGER_LINES" >&2
  echo "  권장: .claude/plans/<slug>.md 작성 + R1~R5 반증형 + 커밋 메시지 plan 경로 인용" >&2
  hook_log "PreToolUse/Bash" "r1r5_plan_check: ⚠ no_plan_ref triggers=${TRIGGER_LINES:0:80}" 2>/dev/null || true
else
  hook_log "PreToolUse/Bash" "r1r5_plan_check: plan_ref OK" 2>/dev/null || true
fi

exit 0
