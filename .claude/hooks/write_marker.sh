#!/bin/bash
# PostToolUse(Edit|Write) — 파일 변경 추적 마커
# completion_gate가 이 마커로 TASKS/HANDOFF 갱신 필요 여부 판단
# v5: python3→bash 전환 (#34457 Windows hooks 멈춤 대응)
source "$(dirname "$0")/hook_common.sh" 2>/dev/null
INPUT=$(cat)

# bash-only JSON 파싱 (python3 의존 제거)
FILE_PATH=$(echo "$INPUT" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
if [ -z "$FILE_PATH" ]; then
  FILE_PATH=$(echo "$INPUT" | sed -n 's/.*"file"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
fi

MARKER="$STATE_AGENT_CONTROL/write_marker.flag"

# 상태문서(TASKS/HANDOFF/STATUS) 수정 → marker 삭제 (갱신 완료 의미)
if echo "$FILE_PATH" | grep -qiE '(TASKS\.md|HANDOFF\.md|STATUS\.md)'; then
  rm -f "$MARKER" 2>/dev/null
  exit 0
fi

# 로그·플래그·CLAUDE.md 등 운영 파일은 마킹 불필요
if echo "$FILE_PATH" | grep -qiE '(CLAUDE\.md|hook_log|\.flag)'; then
  exit 0
fi

# 세션성 .claude/ 하위 경로는 마킹 불필요 (메모리, plans, settings, state 등)
# 단, .claude/hooks/ .claude/rules/ .claude/commands/ 는 핵심 운영 변경이므로 제외하지 않음
if echo "$FILE_PATH" | grep -qE '\.claude/(memory|plans|state|settings)'; then
  exit 0
fi

# 그 외 구현 파일 수정 → marker 생성/갱신
date '+%Y-%m-%d %H:%M:%S' > "$MARKER" 2>/dev/null
