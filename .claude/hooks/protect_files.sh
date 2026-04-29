#!/bin/bash
# PreToolUse(Write|Edit|MultiEdit) hook — 보호 파일 2계층 판정
# deny: 엑셀/기준정보/아카이브 → 즉시 차단
# ask: TASKS.md/HANDOFF.md/STATUS.md → 사용자 확인 요청
#
# 훅 등급: gate (Phase 2-B 2026-04-19 세션72 명시화 + exit 2 전환)

source "$(dirname "$0")/hook_common.sh" 2>/dev/null || true
_PF_START=$(hook_timing_start)

INPUT=$(cat)
# bash-only JSON 파싱 (python3 의존 제거, #34457 Windows hooks 멈춤 대응)
FILE_PATH=$(echo "$INPUT" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
if [ -z "$FILE_PATH" ]; then
  FILE_PATH=$(echo "$INPUT" | sed -n 's/.*"file"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
fi

# hook_config.json에서 설정 읽기 (Phase 2: 중앙 설정형, fallback: 하드코딩)
CONFIG_FILE="$(dirname "$0")/../hook_config.json"
DENY_EXT_PATTERN='\.(xlsx|xls|xlsm|csv|docx|pdf)$'
DENY_PATH_PATTERN='(98_아카이브|기준정보.*최종)'
# 세션128: awk 한 줄 배열 파싱 버그 → python3 안전 파싱으로 교체
if [ -f "$CONFIG_FILE" ] && command -v python3 >/dev/null 2>&1; then
  _cfg=$(python3 -c "
import json,sys
try:
    d=json.load(open(sys.argv[1]))['protect_files']
    exts=[e.lstrip('.') for e in d.get('deny_extensions',[])]
    print('|'.join(exts))
    print('|'.join(d.get('deny_path_patterns',[])))
except Exception: pass
" "$CONFIG_FILE" 2>/dev/null)
  if [ -n "$_cfg" ]; then
    _exts=$(printf '%s\n' "$_cfg" | sed -n '1p')
    _paths=$(printf '%s\n' "$_cfg" | sed -n '2p')
    [ -n "$_exts" ] && DENY_EXT_PATTERN="\\.($_exts)$"
    [ -n "$_paths" ] && DENY_PATH_PATTERN="($_paths)"
  fi
fi

# Layer 1: 즉시 차단 (deny) — config 기반
if echo "$FILE_PATH" | grep -qiE "$DENY_EXT_PATTERN"; then
  echo '{"hookSpecificOutput":{"permissionDecision":"deny","permissionDecisionReason":"원본 파일 직접 수정 금지. 복사본에서 작업하세요."}}'
  hook_timing_end "protect_files" "$_PF_START" "block_ext"
  exit 2
fi

if echo "$FILE_PATH" | grep -qiE "$DENY_PATH_PATTERN"; then
  echo '{"hookSpecificOutput":{"permissionDecision":"deny","permissionDecisionReason":"보호 경로 직접 수정 금지. 사용자 확인 후 진행하세요."}}'
  hook_timing_end "protect_files" "$_PF_START" "block_path"
  exit 2
fi

# Layer 2: 운영 문서 — 자주 수정하지만 주의 필요
# PreToolUse는 allow/deny/ask 모두 지원하나,
# 이번 구현에서는 운영 단순화를 위해 ask 대신 log를 채택
hook_log "PreToolUse" "protect_files: $FILE_PATH" 2>/dev/null || true
hook_timing_end "protect_files" "$_PF_START" "pass"
