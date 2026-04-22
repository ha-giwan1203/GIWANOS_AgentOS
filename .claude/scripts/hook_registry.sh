#!/bin/bash
# hook_registry.sh — [LEGACY / DEPRECATED]
#
# 세션93 (2026-04-22) 2자 토론(Claude × GPT) 합의로 truth chain에서 제외됨.
# 로그: 90_공통기준/토론모드/logs/debate_20260422_150445/plan.md 1주차 1번
#
# 사유:
#   - settings.local.json 전용 파싱 구조. 팀 공용 settings.json 미지원
#   - 현재 저장소는 settings.json(team)에 모든 hooks 등록 + settings.local.json(local) hooks 비어 있음
#   - 본 스크립트 실행 시 31개 중 29개를 WARN으로 잘못 보고
#
# 대체 경로 (Single Source of Truth):
#   - 활성 hook 카운트:    bash .claude/hooks/list_active_hooks.sh --count
#   - 이벤트별 분류:       bash .claude/hooks/list_active_hooks.sh --by-event
#   - 드리프트 검사:       bash .claude/hooks/final_check.sh --fast
#   - README/STATUS 갱신:  list_active_hooks 출력을 참고해 수동 갱신 (자동 sync 중단)
#
# 본 스크립트는 하위호환용으로만 보존. 새 진단 경로에서 호출 금지.
#
# [LEGACY] 기존 사용법:
#   hook_registry.sh check  — [LEGACY] 불일치만 리포트 (settings.local.json만 참조)
#   hook_registry.sh sync   — [LEGACY] settings.local.json 기준으로 갱신 (team settings 환경에서 오답 생성)

set -euo pipefail

# 한국어 경로 안전 처리
export LANG=ko_KR.UTF-8
export LC_ALL=ko_KR.UTF-8

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd -W 2>/dev/null || pwd)"
SETTINGS="$PROJECT_ROOT/.claude/settings.local.json"
README="$PROJECT_ROOT/.claude/hooks/README.md"
STATUS="$PROJECT_ROOT/90_공통기준/업무관리/STATUS.md"
HOOKS_DIR="$PROJECT_ROOT/.claude/hooks"

MODE="${1:-check}"

# --- 보조 스크립트 목록 (settings 등록이지만 직접 hook이 아닌 것) ---
AUX_SCRIPTS="smoke_test.sh"

# --- settings.local.json에서 등록된 hook 파일명 추출 (보조 제외) ---
extract_registered_hooks() {
  grep -oE 'bash \.claude/hooks/[a-zA-Z0-9_]+\.sh' "$SETTINGS" 2>/dev/null \
    | sed 's|bash \.claude/hooks/||' \
    | grep -v "$AUX_SCRIPTS" \
    | sort -u
}

# --- README에서 활성 hook 파일명 추출 ---
extract_readme_hooks() {
  grep -oE '`[a-zA-Z0-9_]+\.sh`' "$README" 2>/dev/null \
    | sed 's/`//g' \
    | grep -v 'hook_common\|smoke_test\|final_check\|smoke_fast\|incident_repair' \
    | sort -u
}

# --- README에서 기재된 hook 수 추출 ---
extract_readme_count() {
  grep -oE '활성 Hook \([0-9]+' "$README" 2>/dev/null | grep -oE '[0-9]+' || echo "0"
}

# --- STATUS에서 hooks 체계 행의 숫자 추출 ---
extract_status_count() {
  grep 'hooks 체계' "$STATUS" 2>/dev/null | grep -oE '[0-9]+' | head -1 || echo "0"
}

# --- 실행 ---
REGISTERED=$(extract_registered_hooks)
REG_COUNT=$(echo "$REGISTERED" | sed '/^$/d' | wc -l | tr -d ' ')
README_HOOKS=$(extract_readme_hooks)
README_COUNT=$(extract_readme_count)
STATUS_COUNT=$(extract_status_count)

# 실파일 존재 확인
MISSING_FILES=""
while IFS= read -r hook; do
  [ -z "$hook" ] && continue
  if [ ! -f "$HOOKS_DIR/$hook" ]; then
    MISSING_FILES="$MISSING_FILES $hook"
  fi
done <<< "$REGISTERED"

# 비교
ONLY_SETTINGS=$(comm -23 <(echo "$REGISTERED") <(echo "$README_HOOKS") | sed '/^$/d')
ONLY_README=$(comm -13 <(echo "$REGISTERED") <(echo "$README_HOOKS") | sed '/^$/d')

echo "=== hook_registry $MODE ==="
echo ""
echo "settings.local.json 등록: ${REG_COUNT}개"
echo "README 활성 표기: ${README_COUNT}개"
echo "STATUS hook 수: ${STATUS_COUNT}개"
echo ""

HAS_ISSUE=0

if [ -n "$MISSING_FILES" ]; then
  echo "[ERROR] settings 등록이나 실파일 없음:$MISSING_FILES"
  HAS_ISSUE=1
fi

if [ -n "$ONLY_SETTINGS" ]; then
  echo "[WARN] settings에만 있음 (README 미기재):"
  echo "$ONLY_SETTINGS" | sed 's/^/  - /'
  HAS_ISSUE=1
fi

if [ -n "$ONLY_README" ]; then
  echo "[WARN] README에만 있음 (settings 미등록):"
  echo "$ONLY_README" | sed 's/^/  - /'
  HAS_ISSUE=1
fi

if [ "$README_COUNT" != "$REG_COUNT" ]; then
  echo "[WARN] README hook 수 불일치: README=${README_COUNT} vs settings=${REG_COUNT}"
  HAS_ISSUE=1
fi

if [ "$STATUS_COUNT" != "$REG_COUNT" ]; then
  echo "[WARN] STATUS hook 수 불일치: STATUS=${STATUS_COUNT} vs settings=${REG_COUNT}"
  HAS_ISSUE=1
fi

if [ "$HAS_ISSUE" -eq 0 ]; then
  echo "[OK] 전체 정합. 불일치 없음."
  exit 0
fi

# --- sync 모드: 자동 갱신 ---
if [ "$MODE" = "sync" ]; then
  echo ""
  echo "--- sync 실행 ---"

  # README hook 수 갱신
  if [ "$README_COUNT" != "$REG_COUNT" ]; then
    sed -i "s/활성 Hook (${README_COUNT}개/활성 Hook (${REG_COUNT}개/" "$README"
    echo "[FIX] README hook 수: ${README_COUNT} → ${REG_COUNT}"
  fi

  # STATUS hook 수 갱신
  if [ "$STATUS_COUNT" != "$REG_COUNT" ]; then
    sed -i "s/\(hooks 체계.*|\s*\)${STATUS_COUNT}개/\1${REG_COUNT}개/" "$STATUS"
    echo "[FIX] STATUS hook 수: ${STATUS_COUNT} → ${REG_COUNT}"
  fi

  echo ""
  echo "sync 완료. README/STATUS 미기재 hook은 수동 추가 필요:"
  if [ -n "$ONLY_SETTINGS" ]; then
    echo "$ONLY_SETTINGS" | sed 's/^/  README 추가 필요: /'
  fi
fi
