#!/bin/bash
# PreToolUse(Write|Edit|MultiEdit) — 신규 파일 위치 화이트리스트 라우팅 gate
#
# 목적: 세션 바뀔 때마다 모델이 임의 위치에 파일 생성하는 sprawl 방지.
# 근거: plan polymorphic-prancing-allen.md (2026-04-28). debate_20260428 외부 의견 통합.
#
# 4-Layer 검증:
#   A. 워크트리 루트 직속 새 파일 — 화이트리스트(CLAUDE.md/README.md/.gitignore 등) 외 deny
#   B. 1단계 폴더 — 13개 도메인 + .claude 외 deny
#   C. 임시 이름 패턴(tmp_/test_/draft_/임시 등) — 도메인 폴더 안에서는 advisory(권고),
#      99_임시수집/98_아카이브는 통과
#   D. .claude 시스템 경로 — 모두 통과
#
# 모드: hook_config.json write_router.mode = "advisory" | "gate"
#   - advisory: stderr 경고만 출력, 차단 없음. 첫 1주 운영용.
#   - gate: deny + exit 2. Day 8+ 전환.
#
# 훅 등급: gate (advisory 모드일 때는 stderr 경고만 — 운영 단계 토글)

source "$(dirname "$0")/hook_common.sh" 2>/dev/null || true
_WR_START=$(hook_timing_start 2>/dev/null || echo 0)

INPUT=$(cat)
# bash-only JSON 파싱 (protect_files.sh와 동일 패턴)
FILE_PATH=$(echo "$INPUT" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
if [ -z "$FILE_PATH" ]; then
  FILE_PATH=$(echo "$INPUT" | sed -n 's/.*"file"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
fi
[ -z "$FILE_PATH" ] && exit 0

# 경로 정규화 (Windows 백슬래시 → 슬래시)
NORM_PATH=$(printf '%s' "$FILE_PATH" | sed 's|\\|/|g')
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
NORM_ROOT=$(printf '%s' "$PROJECT_ROOT" | sed 's|\\|/|g')

# 프로젝트 루트 외부 경로면 통과 (다른 worktree, 시스템 경로 등)
case "$NORM_PATH" in
  "$NORM_ROOT"/*) REL_PATH="${NORM_PATH#"$NORM_ROOT"/}" ;;
  "$NORM_ROOT") exit 0 ;;
  *)
    hook_timing_end "write_router" "$_WR_START" "outside_project" 2>/dev/null
    exit 0
    ;;
esac

# 기존 파일이면 통과 (Edit/MultiEdit는 신규 생성이 아님)
if [ -f "$FILE_PATH" ] || [ -f "$NORM_PATH" ]; then
  hook_timing_end "write_router" "$_WR_START" "existing_file" 2>/dev/null
  exit 0
fi

# hook_config.json에서 설정 읽기 (없으면 하드코딩 fallback)
CONFIG_FILE="$PROJECT_ROOT/.claude/hook_config.json"
MODE="advisory"
ALLOW_ROOT='^(CLAUDE\.md|README\.md|\.gitignore|\.gdignore|\.claudeignore|\.git)$'
ALLOW_DIRS='^(01_인사근태|02_급여단가|03_품번관리|04_생산계획|05_생산실적|06_생산관리|07_라인정지비용|08_공정개선이슈|09_외주발주납품|10_라인배치|90_공통기준|98_아카이브|99_임시수집|\.claude)$'
TEMP_FIRST_RE='^(tmp_|test_|draft_|scratch|temp_|wip_)'
TEMP_SUFFIX_RE='(_temp\.|_draft\.|_review\.|_wip\.)'
TEMP_KEYWORD_RE='(임시|검토중)'
TEMP_ALLOWED='^(99_임시수집|98_아카이브)$'

if [ -f "$CONFIG_FILE" ]; then
  # mode 읽기 (write_router 섹션 한정 — 단순 grep 후 첫 번째 매치)
  _m=$(awk '/"write_router"/{found=1} found && /"mode"/{match($0,/"(advisory|gate)"/,a); print a[1]; exit}' "$CONFIG_FILE" 2>/dev/null)
  [ -n "$_m" ] && MODE="$_m"
fi

# 응답 함수
_deny() {
  local reason="$1"
  if [ "$MODE" = "gate" ]; then
    # JSON deny 응답 (protect_files.sh 패턴)
    printf '{"hookSpecificOutput":{"permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$reason"
    hook_log "write_router" "DENY mode=gate path=$REL_PATH reason=$reason" 2>/dev/null
    hook_timing_end "write_router" "$_WR_START" "deny" 2>/dev/null
    exit 2
  else
    printf '[write_router advisory] %s — %s\n' "$reason" "$REL_PATH" >&2
    hook_log "write_router" "ADVISORY-DENY mode=advisory path=$REL_PATH reason=$reason" 2>/dev/null
    hook_timing_end "write_router" "$_WR_START" "advisory_deny" 2>/dev/null
    exit 0
  fi
}

_advise() {
  local reason="$1"
  printf '[write_router 권고] %s — %s\n' "$reason" "$REL_PATH" >&2
  hook_log "write_router" "ADVISE path=$REL_PATH reason=$reason" 2>/dev/null
  hook_timing_end "write_router" "$_WR_START" "advise" 2>/dev/null
  exit 0
}

_pass() {
  local tag="$1"
  hook_timing_end "write_router" "$_WR_START" "$tag" 2>/dev/null
  exit 0
}

# Layer D: .claude 시스템 경로 — 모두 통과 (이미 protect_files가 보호)
case "$REL_PATH" in
  .claude/*) _pass "system_passthrough" ;;
esac

# 빈 REL_PATH 안전망
[ -z "$REL_PATH" ] && _pass "empty_rel"

# 1단계 분리
FIRST=$(printf '%s' "$REL_PATH" | cut -d/ -f1)

# Layer A: 루트 직속 (REL_PATH에 / 없음)
if [ "$FIRST" = "$REL_PATH" ]; then
  if printf '%s' "$FIRST" | grep -qE "$ALLOW_ROOT"; then
    _pass "allow_root_file"
  fi
  _deny "워크트리 루트에 새 파일 금지. 도메인 폴더(01_인사근태~10_라인배치) / 90_공통기준 / 98_아카이브 / 99_임시수집 / .claude 중 한 곳에 만드세요."
fi

# Layer B: 1단계 폴더 화이트리스트
if ! printf '%s' "$FIRST" | grep -qE "$ALLOW_DIRS"; then
  _deny "신규 폴더 '$FIRST/' 금지. 화이트리스트: 01_인사근태~10_라인배치, 90_공통기준, 98_아카이브, 99_임시수집, .claude. 임시·검토 파일은 99_임시수집/."
fi

# Layer C: 임시 이름 패턴 검사
FILENAME=$(basename "$REL_PATH")
IS_TEMP=0
if printf '%s' "$FILENAME" | grep -qiE "$TEMP_FIRST_RE"; then IS_TEMP=1; fi
if [ $IS_TEMP -eq 0 ] && printf '%s' "$FILENAME" | grep -qiE "$TEMP_SUFFIX_RE"; then IS_TEMP=1; fi
if [ $IS_TEMP -eq 0 ] && printf '%s' "$FILENAME" | grep -qE "$TEMP_KEYWORD_RE"; then IS_TEMP=1; fi

if [ $IS_TEMP -eq 1 ]; then
  if printf '%s' "$FIRST" | grep -qE "$TEMP_ALLOWED"; then
    _pass "temp_in_temp_zone"
  else
    # 도메인 폴더 안 임시 패턴 — Gemini WARN 반영: deny가 아닌 advisory(권고만)
    _advise "임시/검토 이름 패턴은 99_임시수집/ 권장 (도메인 폴더 안 임시 파일은 차단 안 함, 정리 잊지 마세요)"
  fi
fi

# 모든 검사 통과
_pass "pass"
