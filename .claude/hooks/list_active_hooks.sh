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

set -u

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
SETTINGS_TEAM="$PROJECT_DIR/.claude/settings.json"
SETTINGS_LOCAL="$PROJECT_DIR/.claude/settings.local.json"

PY_CMD="python"
command -v python3 >/dev/null 2>&1 && PY_CMD="python3"

MODE="${1:---full}"

"$PY_CMD" - "$SETTINGS_TEAM" "$SETTINGS_LOCAL" "$MODE" <<'PY_END'
import json, sys, os
from collections import defaultdict

mode = sys.argv[3] if len(sys.argv) > 3 else "--full"
events = defaultdict(set)  # event -> set of hook filenames

for f in sys.argv[1:3]:
    if not os.path.exists(f):
        continue
    try:
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        continue
    for evt, handlers in (data.get("hooks") or {}).items():
        for h in handlers or []:
            for hh in (h.get("hooks") or []):
                if hh.get("type") != "command":
                    continue
                cmd = hh.get("command", "")
                # bash .claude/hooks/NAME.sh 패턴만 추출 (statusLine 등 제외)
                if "bash " in cmd and ".claude/hooks/" in cmd:
                    name = cmd.split(".claude/hooks/")[-1].split()[0].strip()
                    if name.endswith(".sh"):
                        events[evt].add(name)

all_names = set()
for names in events.values():
    all_names.update(names)

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
