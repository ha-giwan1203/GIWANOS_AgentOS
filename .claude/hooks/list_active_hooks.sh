#!/bin/bash
# list_active_hooks.sh — settings.json(team+local) 기반 활성 hook 목록 생성 (Single Source)
#
# 세션91 단계 V-1 (2026-04-22) 신설. 원칙 7 Single Source of Truth.
# settings.json이 유일 원본이며, README/STATUS의 훅 숫자는 이 스크립트 출력을 기준으로 동기화한다.
#
# 사용:
#   bash .claude/hooks/list_active_hooks.sh              # 이벤트별 count + 훅 이름 리스트
#   bash .claude/hooks/list_active_hooks.sh --count      # 총합 숫자만 (31)
#   bash .claude/hooks/list_active_hooks.sh --by-event   # 이벤트별 count만
#   bash .claude/hooks/list_active_hooks.sh --names      # 훅 이름만 (sort unique)
#
# 근거: C:/Users/User/.claude/plans/glimmering-churning-reef.md Part 2 원칙 7
#
# M2 (세션96 2자 토론 Round 2 통과 합의): 인라인 settings 파싱을 parse_helpers.py
# `hooks_from_settings`에 위임. 출력 포맷팅은 byte-exact 보존(--count/--names/--by-event/--full
# 4모드 stdout이 변경 전과 1바이트도 다르지 않아야 render_hooks_readme.sh:29 awk -F': '
# 파싱이 깨지지 않음). Claude 독립 추가 5-추가 C 채택 결과.

set -u

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
SETTINGS_TEAM="$PROJECT_DIR/.claude/settings.json"
SETTINGS_LOCAL="$PROJECT_DIR/.claude/settings.local.json"
HELPER="$PROJECT_DIR/.claude/scripts/parse_helpers.py"

PY_CMD="python"
command -v python3 >/dev/null 2>&1 && PY_CMD="python3"

MODE="${1:---full}"

"$PY_CMD" - "$HELPER" "$SETTINGS_TEAM" "$SETTINGS_LOCAL" "$MODE" <<'PY_END'
import json, subprocess, sys

helper, team, local, mode = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
result = subprocess.run(
    [sys.executable, helper, "--op", "hooks_from_settings",
     "--path", team, "--path", local],
    capture_output=True, text=True,
)
if result.returncode != 0:
    sys.stderr.write(result.stderr)
    sys.exit(result.returncode)

data = json.loads(result.stdout)
events = {evt: set(names) for evt, names in data["by_event"].items()}
all_names = set(data["all_names"])

if mode == "--count":
    print(len(all_names))
elif mode == "--names":
    for n in sorted(all_names):
        print(n)
elif mode == "--by-event":
    order = ["PreCompact", "SessionStart", "UserPromptSubmit", "PreToolUse",
             "PostToolUse", "Notification", "Stop"]
    for evt in order:
        if evt in events:
            print(f"{evt}: {len(events[evt])}")
    for evt in sorted(events):
        if evt not in order:
            print(f"{evt}: {len(events[evt])}")
else:
    # --full (기본): 이벤트별 count + 훅 리스트
    order = ["PreCompact", "SessionStart", "UserPromptSubmit", "PreToolUse",
             "PostToolUse", "Notification", "Stop"]
    total = 0
    for evt in order:
        if evt in events:
            names = sorted(events[evt])
            print(f"[{evt}] {len(names)}")
            for n in names:
                print(f"  - {n}")
            total += len(names)
    for evt in sorted(events):
        if evt not in order:
            names = sorted(events[evt])
            print(f"[{evt}] {len(names)}")
            for n in names:
                print(f"  - {n}")
    print()
    print(f"총 고유 hook: {len(all_names)} (event 등록 합: {total})")
PY_END
