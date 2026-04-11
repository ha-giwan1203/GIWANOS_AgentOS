#!/bin/bash
# PostToolUse(Edit|Write) — 파일 변경 추적 마커
# completion_gate가 이 마커로 TASKS/HANDOFF 갱신 필요 여부 판단
# v6: plain timestamp → JSON 메타데이터 (GPT+Claude 합의 2026-04-11)
#   source_class: code|doc|runtime 분류 → completion_gate 오탐 감소
#   after_state_sync: 상태문서 갱신 후 true → 즉시 통과 가능
source "$(dirname "$0")/hook_common.sh" 2>/dev/null
INPUT=$(cat)

# safe_json_get 사용 (sed 단독 파싱 대체)
FILE_PATH=$(echo "$INPUT" | safe_json_get "file_path" 2>/dev/null)
if [ -z "$FILE_PATH" ]; then
  FILE_PATH=$(echo "$INPUT" | safe_json_get "path" 2>/dev/null)
fi

MARKER="$STATE_AGENT_CONTROL/write_marker.json"
LEGACY_MARKER="$STATE_AGENT_CONTROL/write_marker.flag"

# 레거시 .flag 파일 정리
if [ -f "$LEGACY_MARKER" ] && [ ! -f "$MARKER" ]; then
  rm -f "$LEGACY_MARKER" 2>/dev/null
fi

# 상태문서(TASKS/HANDOFF/STATUS) 수정 → marker의 after_state_sync=true로 갱신
if echo "$FILE_PATH" | grep -qiE '(TASKS\.md|HANDOFF\.md|STATUS\.md)'; then
  if [ -f "$MARKER" ]; then
    # 기존 마커의 after_state_sync를 true로 업데이트
    local_ts=$(date '+%Y-%m-%d %H:%M:%S' 2>/dev/null)
    SOURCE_FILE=$(echo "$(cat "$MARKER" 2>/dev/null)" | safe_json_get "source_file" 2>/dev/null || echo "unknown")
    SOURCE_CLASS=$(echo "$(cat "$MARKER" 2>/dev/null)" | safe_json_get "source_class" 2>/dev/null || echo "unknown")
    FILE_PATH_SAFE="$(json_escape "$SOURCE_FILE")"
    printf '{"source_file":"%s","source_class":"%s","created_at":"%s","after_state_sync":true,"session_key":"%s"}\n' \
      "$FILE_PATH_SAFE" "$SOURCE_CLASS" "$local_ts" "$(session_key)" > "$MARKER.tmp" 2>/dev/null && mv -f "$MARKER.tmp" "$MARKER" 2>/dev/null
  fi
  exit 0
fi

# 로그·플래그·CLAUDE.md 등 운영 파일은 마킹 불필요
if echo "$FILE_PATH" | grep -qiE '(CLAUDE\.md|hook_log|\.flag|\.json$)' && echo "$FILE_PATH" | grep -qiE '(hook_log|write_marker|\.flag)'; then
  exit 0
fi
# CLAUDE.md는 마킹 불필요
if echo "$FILE_PATH" | grep -qiE 'CLAUDE\.md$'; then
  exit 0
fi

# 세션성 .claude/ 하위 경로는 마킹 불필요 (메모리, plans, settings, state 등)
# 단, .claude/hooks/ .claude/rules/ .claude/commands/ 는 핵심 운영 변경이므로 제외하지 않음
if echo "$FILE_PATH" | grep -qE '\.claude/(memory|plans|state|settings)'; then
  exit 0
fi

# source_class 분류
SOURCE_CLASS="code"
if echo "$FILE_PATH" | grep -qE '\.claude/(hooks|rules|commands|scripts)/'; then
  SOURCE_CLASS="runtime"
elif echo "$FILE_PATH" | grep -qiE '\.(md|txt|rst)$'; then
  SOURCE_CLASS="doc"
fi

# JSON 메타데이터 마커 생성
local_ts=$(date '+%Y-%m-%d %H:%M:%S' 2>/dev/null)
FILE_PATH_SAFE="$(json_escape "$FILE_PATH")"
printf '{"source_file":"%s","source_class":"%s","created_at":"%s","after_state_sync":false,"session_key":"%s"}\n' \
  "$FILE_PATH_SAFE" "$SOURCE_CLASS" "$local_ts" "$(session_key)" > "$MARKER.tmp" 2>/dev/null && mv -f "$MARKER.tmp" "$MARKER" 2>/dev/null
