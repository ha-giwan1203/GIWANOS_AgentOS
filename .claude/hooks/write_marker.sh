#!/bin/bash
# PostToolUse(Edit|Write) — 파일 변경 추적 마커
# completion_gate가 이 마커로 TASKS/HANDOFF 갱신 필요 여부 판단
# v3: 상태문서 수정 시 marker 삭제 방식 (GPT 토론 합의 2026-04-06)
INPUT=$(cat)

# tool_input에서 file_path 추출
FILE_PATH=$(echo "$INPUT" | bash -c 'read -r line; echo "$line"' | grep -oP '"file_path"\s*:\s*"[^"]*"' | head -1 | grep -oP '(?<=")[^"]+(?="[^"]*$)')

STATE_DIR="${CLAUDE_PROJECT_DIR:-.}/90_공통기준/agent-control/state"
MARKER="$STATE_DIR/write_marker.flag"

# 상태문서(TASKS/HANDOFF/STATUS) 수정 → marker 삭제 (갱신 완료 의미)
if echo "$FILE_PATH" | grep -qiE '(TASKS\.md|HANDOFF\.md|STATUS\.md)'; then
  rm -f "$MARKER" 2>/dev/null
  exit 0
fi

# 로그·플래그·CLAUDE.md 등 운영 파일은 마킹 불필요
if echo "$FILE_PATH" | grep -qiE '(CLAUDE\.md|hook_log|\.flag)'; then
  exit 0
fi

# 그 외 구현 파일 수정 → marker 생성/갱신
date '+%Y-%m-%d %H:%M:%S' > "$MARKER" 2>/dev/null
