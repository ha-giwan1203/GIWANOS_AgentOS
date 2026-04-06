#!/bin/bash
# PostToolUse(Edit|Write) — 구현 파일 변경 시 세션 마커 생성
# completion_gate가 이 마커로 TASKS/HANDOFF 갱신 필요 여부 판단
# v2: python3 제거, 순수 bash (#34457 대응)
INPUT=$(cat)

# tool_input 또는 tool_result에서 file_path 추출 (python3 없이)
FILE_PATH=$(echo "$INPUT" | bash -c 'read -r line; echo "$line"' | grep -oP '"file_path"\s*:\s*"[^"]*"' | head -1 | grep -oP '(?<=")[^"]+(?="[^"]*$)')

# 운영 문서·로그·상태 파일은 마킹 제외
if echo "$FILE_PATH" | grep -qiE '(TASKS\.md|HANDOFF\.md|STATUS\.md|CLAUDE\.md|hook_log|\.flag|\.json$)'; then
  exit 0
fi

STATE_DIR="${CLAUDE_PROJECT_DIR:-.}/90_공통기준/agent-control/state"
MARKER="$STATE_DIR/write_marker.flag"

# marker가 이미 있으면 덮어쓰지 않음 (completion_gate 통과 시 삭제됨)
# → TASKS/HANDOFF 편집 후 다른 파일 편집해도 marker 갱신 안 됨 → 루프 방지
if [ ! -f "$MARKER" ]; then
  date '+%Y-%m-%d %H:%M:%S' > "$MARKER" 2>/dev/null
fi
