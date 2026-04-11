#!/bin/bash
# publish_worktree_to_main.sh — 워크트리 브랜치 → main 반영 (B-lite)
# 세션 10 합의: cherry-pick/ff + clean 검사 + --dry-run
# 2026-04-11

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# hook_common.sh 로드 (git_has_relevant_changes 등 재사용)
source "$SCRIPT_DIR/../hooks/hook_common.sh" 2>/dev/null || true

# --- 옵션 파싱 ---
MODE="ff-only"   # 기본값
DRY_RUN=false

usage() {
  cat <<EOF
사용법: publish_worktree_to_main.sh [옵션]

워크트리 브랜치의 커밋을 main에 반영한다.

옵션:
  --ff-only      fast-forward만 허용 (기본값)
  --cherry-pick  cherry-pick으로 반영
  --dry-run      검사만 수행, 실제 반영 안 함
  -h, --help     이 도움말 표시

필수 조건:
  - 워크트리에서 실행해야 함 (main 브랜치 직접 실행 불가)
  - 미커밋 변경 없어야 함 (clean 상태)
EOF
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ff-only)      MODE="ff-only"; shift ;;
    --cherry-pick)  MODE="cherry-pick"; shift ;;
    --dry-run)      DRY_RUN=true; shift ;;
    -h|--help)      usage ;;
    *)              echo "알 수 없는 옵션: $1"; usage ;;
  esac
done

# --- 사전 검사 ---

# 1. 현재 브랜치 확인
CURRENT_BRANCH=$(git -C "$PROJECT_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null)
if [ "$CURRENT_BRANCH" = "main" ]; then
  echo "오류: main 브랜치에서는 실행할 수 없습니다. 워크트리에서 실행하세요."
  exit 1
fi

echo "현재 브랜치: $CURRENT_BRANCH"
echo "반영 모드: $MODE"
$DRY_RUN && echo "드라이런 모드: 실제 반영 안 함"

# 2. clean 상태 확인
cd "$PROJECT_ROOT"
if git_has_relevant_changes 2>/dev/null; then
  echo "오류: 미커밋 변경이 있습니다. 커밋 또는 stash 후 재시도하세요."
  git_relevant_change_list 2>/dev/null | head -10
  exit 1
fi
echo "clean 상태 확인: OK"

# 3. main과의 차이 확인
COMMITS_AHEAD=$(git rev-list --count main..HEAD 2>/dev/null || echo "0")
COMMITS_BEHIND=$(git rev-list --count HEAD..main 2>/dev/null || echo "0")

echo "main 대비: +${COMMITS_AHEAD} ahead / -${COMMITS_BEHIND} behind"

if [ "$COMMITS_AHEAD" = "0" ]; then
  echo "main에 반영할 커밋이 없습니다."
  exit 0
fi

# unique patch 확인
UNIQUE_PATCHES=$(git cherry -v main HEAD 2>/dev/null | grep -c '^+' || echo "0")
echo "unique patch: ${UNIQUE_PATCHES}건"

if [ "$UNIQUE_PATCHES" = "0" ]; then
  echo "main에 이미 모든 패치가 반영되어 있습니다."
  exit 0
fi

# 반영 대상 커밋 표시
echo ""
echo "=== 반영 대상 커밋 ==="
git cherry -v main HEAD 2>/dev/null | grep '^+'
echo ""

# --- 드라이런 종료 ---
if $DRY_RUN; then
  echo "[드라이런] 실제 반영 없이 종료합니다."
  exit 0
fi

# --- 메인 저장소 경로 확인 ---
# 워크트리에서는 git checkout main이 불가(다른 워크트리가 main 사용 중)
# 따라서 메인 저장소 경로에서 -C 옵션으로 cherry-pick 수행
MAIN_REPO=$(git rev-parse --git-common-dir 2>/dev/null | sed 's|/.git$||; s|/.git/worktrees/.*||')
if [ -z "$MAIN_REPO" ] || [ ! -d "$MAIN_REPO" ]; then
  # fallback: PROJECT_ROOT의 부모에서 .git 찾기
  MAIN_REPO=$(cd "$PROJECT_ROOT" && git worktree list 2>/dev/null | head -1 | awk '{print $1}')
fi

if [ -z "$MAIN_REPO" ] || [ ! -d "$MAIN_REPO" ]; then
  echo "오류: 메인 저장소 경로를 찾을 수 없습니다."
  exit 1
fi

echo "메인 저장소: $MAIN_REPO"

# main 브랜치가 메인 저장소에서 체크아웃 중인지 확인
MAIN_BRANCH=$(git -C "$MAIN_REPO" rev-parse --abbrev-ref HEAD 2>/dev/null)
if [ "$MAIN_BRANCH" != "main" ]; then
  echo "오류: 메인 저장소가 main 브랜치가 아닙니다 ($MAIN_BRANCH)"
  exit 1
fi

# --- 반영 실행 ---

case "$MODE" in
  ff-only)
    echo "=== fast-forward 반영 시작 ==="
    if git -C "$MAIN_REPO" merge --ff-only "$CURRENT_BRANCH" 2>/dev/null; then
      NEW_SHA=$(git -C "$MAIN_REPO" rev-parse --short HEAD)
      echo "fast-forward 완료: main → $NEW_SHA"
    else
      echo "오류: fast-forward 불가. main이 분기되었습니다."
      echo "cherry-pick 모드(--cherry-pick)를 사용하세요."
      exit 1
    fi
    ;;

  cherry-pick)
    echo "=== cherry-pick 반영 시작 ==="
    # unique patch만 추출
    PICK_SHAS=$(git cherry -v main HEAD 2>/dev/null | grep '^+' | awk '{print $2}')

    PICK_COUNT=0
    for sha in $PICK_SHAS; do
      if git -C "$MAIN_REPO" cherry-pick "$sha" 2>/dev/null; then
        PICK_COUNT=$((PICK_COUNT + 1))
        echo "  cherry-pick: $sha OK"
      else
        echo "오류: cherry-pick 충돌 — $sha"
        echo "수동 해결: cd $MAIN_REPO && git cherry-pick --abort"
        exit 1
      fi
    done

    NEW_SHA=$(git -C "$MAIN_REPO" rev-parse --short HEAD)
    echo "cherry-pick 완료: ${PICK_COUNT}건 반영, main → $NEW_SHA"
    ;;
esac

# --- push ---
echo ""
echo "=== push ==="
if git -C "$MAIN_REPO" push origin main 2>&1; then
  FINAL_SHA=$(git -C "$MAIN_REPO" rev-parse --short HEAD)
  echo ""
  echo "반영 완료"
  echo "  브랜치: $CURRENT_BRANCH → main"
  echo "  모드: $MODE"
  echo "  SHA: $FINAL_SHA"
  echo "  git show --stat:"
  git -C "$MAIN_REPO" show --stat --oneline HEAD
else
  echo "오류: push 실패"
  exit 1
fi
