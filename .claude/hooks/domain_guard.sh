#!/bin/bash
# PreToolUse hook — 도메인 CLAUDE.md 미로드 시 도구 실행 차단 (화이트리스트 방식)
# 정책: domain_guard_config.yaml (단일 기준)
# v3.2: Python 로직 분리 (.py 파일) — bash 인라인 따옴표 해석 문제 제거

source "$(dirname "$0")/hook_common.sh" 2>/dev/null
INPUT=$(cat)
hook_log "PreToolUse" "domain_guard 발화"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/domain_guard_config.yaml"

if [ ! -f "$CONFIG" ]; then
  exit 0
fi

# Python 로직은 별도 .py 파일로 분리 (bash 따옴표 해석 문제 근본 제거)
RESULT=$(echo "$INPUT" | PYTHONIOENCODING=utf-8 python3 "$SCRIPT_DIR/domain_guard_logic.py" "$CONFIG" 2>/dev/null)

if [ -n "$RESULT" ]; then
  echo "$RESULT"
fi

exit 0
