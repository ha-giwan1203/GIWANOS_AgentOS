#!/bin/bash
# render_hooks_readme.sh — README.md / STATUS.md 훅 숫자 자동 갱신 (Single Source)
#
# 세션91 단계 V-2 (2026-04-22) 신설. 원칙 7 Single Source of Truth.
# settings.json이 유일 원본. 문서의 숫자 서술을 list_active_hooks.sh 출력으로 갱신한다.
#
# 사용:
#   bash .claude/hooks/render_hooks_readme.sh         # README.md + STATUS.md 갱신
#   bash .claude/hooks/render_hooks_readme.sh --dry   # 갱신 없이 차이만 표시
#
# 동작: 정규식 치환으로 "N개 등록" / "= **N**" 형태만 교체. 테이블 본문은 손대지 않음.
# 수동 README 테이블 항목은 별개로 유지 — 숫자 드리프트만 구조적 해소.

set -u

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
HOOKS_DIR="$PROJECT_DIR/.claude/hooks"
README="$HOOKS_DIR/README.md"
STATUS="$PROJECT_DIR/90_공통기준/업무관리/STATUS.md"

DRY=0
[ "${1:-}" = "--dry" ] && DRY=1

# 활성 hook 수 + 이벤트별 카운트 수집
COUNT=$(bash "$HOOKS_DIR/list_active_hooks.sh" --count)
BY_EVENT=$(bash "$HOOKS_DIR/list_active_hooks.sh" --by-event)

# 이벤트별 요약 한 줄 (PreCompact 1 / SessionStart 1 / ... = 31)
EVENT_LINE=$(echo "$BY_EVENT" | awk -F': ' '{printf "%s %s / ", $1, $2}' | sed 's# / $##')
EVENT_LINE="${EVENT_LINE} = **${COUNT}**"

echo "== render_hooks_readme =="
echo "COUNT: $COUNT"
echo "EVENT_LINE: $EVENT_LINE"
echo ""

# README.md 갱신: 헤더 "## 활성 Hook (N개 등록" + 이벤트 요약 라인
if [ -f "$README" ]; then
  if [ "$DRY" = "1" ]; then
    echo "--- README.md (dry) ---"
    grep -E '^## 활성 Hook \([0-9]+개 등록|^> 이벤트별 등록 수:' "$README"
  else
    sed -i -E "s|^(## 활성 Hook \()[0-9]+(개 등록.*)|\1${COUNT}\2|" "$README"
    sed -i -E "s|^(> 이벤트별 등록 수: ).*|\1${EVENT_LINE}|" "$README"
    echo "README.md 갱신 완료"
  fi
fi

# STATUS.md 갱신: "| hooks 체계 | N개 등록"
if [ -f "$STATUS" ]; then
  if [ "$DRY" = "1" ]; then
    echo "--- STATUS.md (dry) ---"
    grep -E '\| hooks 체계 \| [0-9]+개 등록' "$STATUS"
  else
    sed -i -E "s|(\\| hooks 체계 \\| )[0-9]+(개 등록)|\1${COUNT}\2|" "$STATUS"
    echo "STATUS.md 갱신 완료"
  fi
fi

echo ""
echo "완료: 활성 ${COUNT}개 기준 동기화"
