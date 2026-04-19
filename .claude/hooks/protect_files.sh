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
if [ -f "$CONFIG_FILE" ]; then
  # deny_extensions: JSON 배열에서 확장자만 추출 (awk로 배열 경계 안전 파싱)
  _exts=$(awk '/"deny_extensions"/{found=1;next} found && /\]/{exit} found && /"\.[^"]*"/{gsub(/.*"\./, ""); gsub(/".*/, ""); print}' "$CONFIG_FILE" 2>/dev/null | tr '\n' '|' | sed 's/|$//')
  [ -n "$_exts" ] && DENY_EXT_PATTERN="\\.($_exts)$"
  # deny_path_patterns: JSON 배열에서 패턴만 추출
  _paths=$(awk '/"deny_path_patterns"/{found=1;next} found && /\]/{exit} found && /"[^"]*"/{gsub(/.*"/, ""); gsub(/".*/, ""); print}' "$CONFIG_FILE" 2>/dev/null | tr '\n' '|' | sed 's/|$//')
  [ -n "$_paths" ] && DENY_PATH_PATTERN="($_paths)"
fi

# Layer 1: 즉시 차단 (deny) — config 기반
if echo "$FILE_PATH" | grep -qiE "$DENY_EXT_PATTERN"; then
  echo '{"decision":"deny","reason":"원본 파일 직접 수정 금지. 복사본에서 작업하세요."}'
  hook_timing_end "protect_files" "$_PF_START" "block_ext"
  exit 2
fi

if echo "$FILE_PATH" | grep -qiE "$DENY_PATH_PATTERN"; then
  echo '{"decision":"deny","reason":"보호 경로 직접 수정 금지. 사용자 확인 후 진행하세요."}'
  hook_timing_end "protect_files" "$_PF_START" "block_path"
  exit 2
fi

# Layer 2: 운영 문서 — 자주 수정하지만 주의 필요
# PreToolUse는 allow/deny/ask 모두 지원하나,
# 이번 구현에서는 운영 단순화를 위해 ask 대신 log를 채택
hook_log "PreToolUse" "protect_files: $FILE_PATH" 2>/dev/null || true
hook_timing_end "protect_files" "$_PF_START" "pass"
