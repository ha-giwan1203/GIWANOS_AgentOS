#!/bin/bash
# PreToolUse(Write|Edit|MultiEdit) hook — 보호 파일 2계층 판정
# deny: 엑셀/기준정보/아카이브 → 즉시 차단
# ask: TASKS.md/HANDOFF.md/STATUS.md → 사용자 확인 요청

INPUT=$(cat)
# bash-only JSON 파싱 (python3 의존 제거, #34457 Windows hooks 멈춤 대응)
FILE_PATH=$(echo "$INPUT" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
if [ -z "$FILE_PATH" ]; then
  FILE_PATH=$(echo "$INPUT" | sed -n 's/.*"file"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
fi

# Layer 1: 즉시 차단 (deny)
if echo "$FILE_PATH" | grep -qiE '\.(xlsx|xls|xlsm|csv|docx|pdf)$'; then
  echo '{"decision":"deny","reason":"원본 파일 직접 수정 금지. 복사본에서 작업하세요."}'
  exit 0
fi

if echo "$FILE_PATH" | grep -qi '98_아카이브'; then
  echo '{"decision":"deny","reason":"아카이브 폴더 직접 수정 금지."}'
  exit 0
fi

if echo "$FILE_PATH" | grep -qi '기준정보.*최종'; then
  echo '{"decision":"deny","reason":"기준정보 원본 파일 수정 금지. 사용자 확인 후 진행하세요."}'
  exit 0
fi

# Layer 2: 운영 문서 — 자주 수정하지만 주의 필요
# PreToolUse는 allow/deny/ask 모두 지원하나,
# 이번 구현에서는 운영 단순화를 위해 ask 대신 log를 채택

source "$(dirname "$0")/hook_common.sh" 2>/dev/null || true
hook_log "PreToolUse" "protect_files: $FILE_PATH" 2>/dev/null || true
