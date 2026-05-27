#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PreToolUse gate — Codex 위임 채널 단일 디폴트 강제.

차단 조건:
1) Agent tool 호출 + subagent_type == 'codex:codex-rescue'
2) Bash tool 호출 + command 에 'codex exec' 토큰 포함 (auto_reply.py 경로 호출은 통과)

차단 시 stderr 안내 + exit 2 (decision: block).
정상 통과는 exit 0.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Claude Code PreToolUse 입력: stdin에 JSON
# {"tool_name": "...", "tool_input": {...}}

ALLOWED_CODEX_CHANNEL = (
    "python 90_공통기준/업무관리/codex_claude_channel/auto_reply.py "
    "--target codex \"<지시문>\""
)


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # gate 자체 실패는 통과 (advisory 폴백)

    tool = data.get("tool_name") or data.get("tool") or ""
    tin = data.get("tool_input") or {}

    # 1) Agent tool — codex:codex-rescue 차단
    if tool == "Agent":
        st = (tin.get("subagent_type") or "").strip().lower()
        if st == "codex:codex-rescue":
            sys.stderr.write(
                "[delegate_channel_gate] BLOCK: Agent subagent_type='codex:codex-rescue' "
                "는 사용자 미확인 백그라운드 채널이라 금지.\n"
                f"대신 사용: {ALLOWED_CODEX_CHANNEL}\n"
                "근거: feedback_codex_channel_default.md\n"
            )
            return 2

    # 2) Bash — codex exec 헤드리스 차단 (auto_reply.py 경로는 통과)
    if tool == "Bash":
        cmd = (tin.get("command") or "")
        low = cmd.lower()
        if "auto_reply.py" in low:
            return 0
        # 'codex exec' 또는 'codex exec resume' 패턴 차단
        if " codex exec" in (" " + low) or low.startswith("codex exec"):
            sys.stderr.write(
                "[delegate_channel_gate] BLOCK: 'codex exec' 헤드리스 직접 호출 금지.\n"
                f"대신 사용: {ALLOWED_CODEX_CHANNEL}\n"
                "근거: feedback_codex_channel_default.md\n"
            )
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
