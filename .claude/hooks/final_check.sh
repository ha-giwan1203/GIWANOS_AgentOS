#!/bin/bash
# final_check.sh — 커밋 전 자체검증 (commit_gate에서 자동 호출)
# --fast: 교차검증만 (매 커밋/푸시), --full: fast + smoke_test (hook/settings 변경 시)
# 기본값: --full (수동 실행 시)
# GPT+Claude 합의 2026-04-07

# 인자 파싱: --fast, --full, --fix (자동 교정)
MODE="--full"
FIX_MODE=false
for arg in "$@"; do
  case "$arg" in
    --fast) MODE="--fast" ;;
    --full) MODE="--full" ;;
    --fix)  FIX_MODE=true ;;
  esac
done
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
HOOKS_DIR="$PROJECT_DIR/.claude/hooks"
export CLAUDE_PROJECT_DIR="$PROJECT_DIR"
source "$HOOKS_DIR/hook_common.sh" 2>/dev/null || true
FAIL=0
WARN=0
SETTINGS="$PROJECT_DIR/.claude/settings.local.json"
README_FILE="$HOOKS_DIR/README.md"
STATUS_FILE="$PROJECT_DIR/90_공통기준/업무관리/STATUS.md"
TASKS="$PROJECT_DIR/90_공통기준/업무관리/TASKS.md"
HANDOFF="$PROJECT_DIR/90_공통기준/업무관리/HANDOFF.md"

warn() {
  echo "  [WARN] $1"
  WARN=$((WARN+1))
}

fail() {
  echo "  [FAIL] $1"
  FAIL=$((FAIL+1))
}

registered_hook_names() {
  local settings_file="${1:-$SETTINGS}"
  if [ ! -f "$settings_file" ]; then
    return 1
  fi
  grep -oE '"command"[[:space:]]*:[[:space:]]*"bash \.claude/hooks/[A-Za-z0-9_-]+\.sh"' "$settings_file" 2>/dev/null \
    | sed -E 's/.*\/([A-Za-z0-9_-]+\.sh)".*/\1/' \
    | sort -u
}

readme_active_hook_count() {
  local readme_file="${1:-$README_FILE}"
  if [ ! -f "$readme_file" ]; then
    return 1
  fi
  awk '/^## 활성 Hook/{flag=1; next} /^## (훅별 실패|보조 스크립트)/{flag=0} flag' "$readme_file" 2>/dev/null \
    | grep -c '^| .*`[A-Za-z0-9_-]\+\.sh` .*|'
}

# README에서 개별 훅 이름 추출 (세션 11: 이름 대조 lint용)
readme_active_hook_names() {
  local readme_file="${1:-$README_FILE}"
  if [ ! -f "$readme_file" ]; then
    return 1
  fi
  awk '/^## 활성 Hook/{flag=1; next} /^## (훅별 실패|보조 스크립트)/{flag=0} flag' "$readme_file" 2>/dev/null \
    | grep -oE '`[A-Za-z0-9_-]+\.sh`' \
    | sed 's/`//g' \
    | sort -u
}

status_hook_count() {
  local status_file="${1:-$STATUS_FILE}"
  local line
  if [ ! -f "$status_file" ]; then
    return 1
  fi
  line=$(grep -F '| hooks 체계 |' "$status_file" 2>/dev/null | head -1)
  if [ -z "$line" ]; then
    return 1
  fi
  printf '%s' "$line" | sed -n 's/.*| hooks 체계 |[^0-9]*\([0-9][0-9]*\)개 등록.*/\1/p'
}

echo "=== Final Check ($MODE) ==="
echo ""

# === FAST 구간: 교차검증 (매 커밋 필수) ===

# 1. 구 로그 직접 참조 잔존 확인
echo "--- 1. 구 로그 직접 참조 잔존 확인 ---"
STALE=$(grep -rl 'hook_log\.txt' "$HOOKS_DIR"/*.sh 2>/dev/null | grep -v smoke_test.sh | grep -v final_check.sh)
if [ -n "$STALE" ]; then
  echo "  [FAIL] hook_log.txt 직접 참조 잔존: $STALE"
  FAIL=$((FAIL+1))
else
  echo "  [OK] hook_log.txt 직접 참조 0건"
fi
echo ""

# 2. python3 잔존 참조 확인
echo "--- 2. python3 잔존 참조 확인 ---"
PY3_REFS=$(grep -l 'python3 -c\|python3 -' "$HOOKS_DIR"/*.sh 2>/dev/null | grep -v smoke_test.sh | grep -v final_check.sh | grep -v auto_compile.sh | grep -v _archive)
if [ -n "$PY3_REFS" ]; then
  warn "python3 의존 잔존:"
  echo "$PY3_REFS" | while read f; do echo "    - $(basename $f)"; done
else
  echo "  [OK] 운영 훅 python3 의존 0건 (auto_compile 제외)"
fi
echo ""

# 3. 실등록 hook 개수 vs 문서 정합성 확인
echo "--- 3. hook 개수 정합성 ---"
REGISTERED_HOOKS=$(registered_hook_names)
if [ -n "$REGISTERED_HOOKS" ]; then
  SETTINGS_HOOKS=$(printf '%s\n' "$REGISTERED_HOOKS" | sed '/^$/d' | wc -l | tr -d ' ')
  echo "  settings.local 실등록: ${SETTINGS_HOOKS}개"
else
  SETTINGS_HOOKS=""
  warn "settings.local.json에서 활성 hook 목록을 읽지 못함"
fi

README_COUNT=$(readme_active_hook_count 2>/dev/null || true)
STATUS_COUNT=$(status_hook_count 2>/dev/null || true)

if [ -n "$README_COUNT" ]; then
  echo "  README 문서화: ${README_COUNT}개"
  if [ -n "$SETTINGS_HOOKS" ] && [ "$README_COUNT" -ne "$SETTINGS_HOOKS" ] 2>/dev/null; then
    if $FIX_MODE; then
      echo "  [FIX] hook_registry.sh sync 실행..."
      bash "$PROJECT_DIR/.claude/scripts/hook_registry.sh" sync 2>&1 | sed 's/^/    /'
      echo "  [FIX] 완료. README/STATUS hook 수 자동 갱신됨"
    elif [ "$MODE" = "--full" ]; then
      fail "README($README_COUNT) ≠ settings.local($SETTINGS_HOOKS) — 문서 드리프트 (--full 모드: FAIL 승격). --fix로 자동 교정 가능"
    else
      warn "README($README_COUNT) ≠ settings.local($SETTINGS_HOOKS) — 문서 드리프트"
    fi
    # 개별 훅 이름 대조 (세션 11 lint 개선)
    README_HOOKS=$(readme_active_hook_names 2>/dev/null || true)
    if [ -n "$README_HOOKS" ] && [ -n "$REGISTERED_HOOKS" ]; then
      ONLY_SETTINGS=$(comm -23 <(printf '%s\n' "$REGISTERED_HOOKS") <(printf '%s\n' "$README_HOOKS") 2>/dev/null)
      ONLY_README=$(comm -13 <(printf '%s\n' "$REGISTERED_HOOKS") <(printf '%s\n' "$README_HOOKS") 2>/dev/null)
      if [ -n "$ONLY_SETTINGS" ]; then
        echo "    settings에만 있음: $ONLY_SETTINGS"
      fi
      if [ -n "$ONLY_README" ]; then
        echo "    README에만 있음: $ONLY_README"
      fi
    fi
  else
    echo "  [OK] README hook 개수 일치"
  fi
else
  warn "README 활성 hook 개수를 읽지 못함"
fi

if [ -n "$STATUS_COUNT" ]; then
  echo "  STATUS 문서화: ${STATUS_COUNT}개"
  if [ -n "$SETTINGS_HOOKS" ] && [ "$STATUS_COUNT" -ne "$SETTINGS_HOOKS" ] 2>/dev/null; then
    if [ "$MODE" = "--full" ]; then
      fail "STATUS($STATUS_COUNT) ≠ settings.local($SETTINGS_HOOKS) — 문서 드리프트 (--full 모드: FAIL 승격)"
    else
      warn "STATUS($STATUS_COUNT) ≠ settings.local($SETTINGS_HOOKS) — 문서 드리프트"
    fi
  else
    echo "  [OK] STATUS hook 개수 일치"
  fi
else
  warn "STATUS hooks 체계 행에서 개수를 읽지 못함"
fi
echo ""

# 4. HANDOFF 계획 vs 실물 교차확인
echo "--- 4. HANDOFF 계획 vs 실물 교차확인 ---"
if grep -q 'cp' "$HOOKS_DIR/block_dangerous.sh" 2>/dev/null; then
  echo "  [OK] block_dangerous DANGER_CMDS에 cp 포함"
else
  warn "block_dangerous DANGER_CMDS에 cp 누락"
fi
echo ""

# 5. settings.local 등록 hook 실존 여부
echo "--- 5. settings.local 등록 hook 실존 여부 ---"
if [ -n "$REGISTERED_HOOKS" ]; then
  MISSING_REGISTERED=""
  while IFS= read -r hook_name; do
    [ -z "$hook_name" ] && continue
    if [ ! -f "$HOOKS_DIR/$hook_name" ]; then
      MISSING_REGISTERED="${MISSING_REGISTERED}${hook_name}"$'\n'
    fi
  done <<EOF
$REGISTERED_HOOKS
EOF

  if [ -n "$MISSING_REGISTERED" ]; then
    fail "settings.local 등록 훅 파일 누락:"
    printf '%s' "$MISSING_REGISTERED" | while IFS= read -r hook_name; do
      [ -n "$hook_name" ] && echo "    - $hook_name"
    done
  else
    echo "  [OK] settings.local 등록 훅 실파일 모두 존재"
  fi
else
  warn "settings.local 등록 훅 실존 여부 검사 건너뜀"
fi
echo ""

# 6. 상태 문서 3종 날짜 동기화 확인 (staged 우선, 없으면 working tree)
echo "--- 6. TASKS/HANDOFF/STATUS 날짜 동기화 ---"
# staged snapshot에서 날짜 추출 시도, 없으면 working tree fallback
_get_date() {
  local rel_path="$1"
  local staged_content
  staged_content=$(cd "$PROJECT_DIR" && git show :"$rel_path" 2>/dev/null)
  if [ -n "$staged_content" ]; then
    echo "$staged_content" | sed -n 's/.*최종 업데이트: \([0-9-]*\).*/\1/p' | head -1
  else
    sed -n 's/.*최종 업데이트: \([0-9-]*\).*/\1/p' "$PROJECT_DIR/$rel_path" 2>/dev/null | head -1
  fi
}

TASKS_DATE=$(_get_date "90_공통기준/업무관리/TASKS.md")
HANDOFF_DATE=$(_get_date "90_공통기준/업무관리/HANDOFF.md")
STATUS_DATE=$(_get_date "90_공통기준/업무관리/STATUS.md")
echo "  TASKS: $TASKS_DATE / HANDOFF: $HANDOFF_DATE / STATUS: $STATUS_DATE"

if [ -n "$TASKS_DATE" ] && [ -n "$STATUS_DATE" ]; then
  if [[ "$STATUS_DATE" < "$TASKS_DATE" ]]; then
    fail "STATUS($STATUS_DATE) < TASKS($TASKS_DATE) — STATUS.md 드리프트"
    hook_incident "gate_reject" "final_check" "STATUS.md" "meta_drift: STATUS($STATUS_DATE) < TASKS($TASKS_DATE)" '"classification_reason":"meta_drift"'
  else
    echo "  [OK] STATUS 날짜 >= TASKS 날짜"
  fi
fi
if [ -n "$TASKS_DATE" ] && [ -n "$HANDOFF_DATE" ]; then
  if [[ "$HANDOFF_DATE" < "$TASKS_DATE" ]]; then
    warn "HANDOFF($HANDOFF_DATE) < TASKS($TASKS_DATE) — HANDOFF 드리프트"
    hook_incident "gate_reject" "final_check" "HANDOFF.md" "meta_drift: HANDOFF($HANDOFF_DATE) < TASKS($TASKS_DATE)" '"classification_reason":"meta_drift"'
  else
    echo "  [OK] HANDOFF 날짜 >= TASKS 날짜"
  fi
fi

# 6b. 세션 번호 비교 (세션46 GPT 합의: 같은 날 세션 드리프트 감지)
_get_session() {
  local rel_path="$1"
  local content
  content=$(cd "$PROJECT_DIR" && git show :"$rel_path" 2>/dev/null)
  [ -z "$content" ] && content=$(cat "$PROJECT_DIR/$rel_path" 2>/dev/null)
  echo "$content" | grep -oE '세션[0-9]+' | head -1 | grep -oE '[0-9]+'
}
TASKS_SESSION=$(_get_session "90_공통기준/업무관리/TASKS.md")
HANDOFF_SESSION=$(_get_session "90_공통기준/업무관리/HANDOFF.md")
echo "  TASKS 세션: $TASKS_SESSION / HANDOFF 세션: $HANDOFF_SESSION"
if [ -n "$TASKS_SESSION" ] && [ -n "$HANDOFF_SESSION" ]; then
  if [ "$HANDOFF_SESSION" -lt "$TASKS_SESSION" ] 2>/dev/null; then
    warn "HANDOFF(세션$HANDOFF_SESSION) < TASKS(세션$TASKS_SESSION) — 세션 드리프트"
  else
    echo "  [OK] HANDOFF 세션 >= TASKS 세션"
  fi
fi
echo ""

# 7. TASKS/HANDOFF 최신화 확인
echo "--- 7. TASKS/HANDOFF 갱신 확인 ---"
STATE_DIR="$PROJECT_DIR/90_공통기준/agent-control/state"
MARKER="$STATE_DIR/write_marker.json"
LEGACY_MARKER="$STATE_DIR/write_marker.flag"
# 레거시 .flag 파일도 확인 (마이그레이션 기간)
if [ ! -f "$MARKER" ] && [ -f "$LEGACY_MARKER" ]; then
  MARKER="$LEGACY_MARKER"
fi

if [ -f "$MARKER" ]; then
  # after_state_sync=true면 상태문서 갱신 완료 — skip (completion_gate와 동일 판정)
  AFTER_SYNC=$(safe_json_get "after_state_sync" < "$MARKER" 2>/dev/null)
  if [ "$AFTER_SYNC" = "true" ]; then
    echo "  [OK] after_state_sync=true — 상태문서 갱신 완료"
  else
    # write_marker.json의 created_at 필드 우선, 없으면 mtime fallback (마커 해석 통일, 세션 11)
    MARKER_CREATED=$(safe_json_get "created_at" < "$MARKER" 2>/dev/null || echo "")
    if [ -n "$MARKER_CREATED" ]; then
      MARKER_EPOCH=$(date -d "$MARKER_CREATED" +%s 2>/dev/null || file_mtime "$MARKER")
    else
      MARKER_EPOCH=$(file_mtime "$MARKER")
    fi
    for F in "$TASKS" "$HANDOFF" "$STATUS_FILE"; do
      NAME=$(basename "$F")
      if [ -f "$F" ]; then
        F_EPOCH=$(file_mtime "$F")
        if [ "$F_EPOCH" -lt "$MARKER_EPOCH" ] 2>/dev/null; then
          fail "$NAME — write_marker 이후 미갱신"
        else
          echo "  [OK] $NAME 갱신됨"
        fi
      else
        fail "$NAME 파일 없음"
      fi
    done
  fi
else
  echo "  [INFO] write_marker 없음 (파일 변경 없는 세션)"
fi
echo ""

# === FULL 구간: smoke_test (--full 시에만) ===

if [ "$MODE" = "--full" ]; then
  echo "--- 8. smoke_test 실행 ---"
  bash "$HOOKS_DIR/smoke_test.sh"
  if [ $? -ne 0 ]; then
    FAIL=$((FAIL+1))
  fi
  echo ""

  echo "--- 9. 미커밋 변경 파일 ---"
  CHANGES=$(git_relevant_change_list)
  if [ -z "$CHANGES" ]; then
    echo "  [INFO] 변경 파일 없음"
  else
    echo "$CHANGES" | sort -u | while read f; do
      [ -n "$f" ] && echo "  - $f"
    done
  fi
  echo ""
fi

# === 결과 ===
if [ "$FAIL" -gt 0 ]; then
  echo "=== FAIL: $FAIL건 미해결 / WARN: $WARN건. ==="
  exit 1
elif [ "$WARN" -gt 0 ]; then
  echo "=== WARN: $WARN건 경고. 커밋은 허용되지만 확인 권장. ==="
  exit 0
else
  echo "=== ALL CLEAR. ==="
  exit 0
fi
