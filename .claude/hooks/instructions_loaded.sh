#!/bin/bash
# InstructionsLoaded hook — CLAUDE.md / rules 로드 관측
INPUT=$(cat)
FILE=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('file','unknown'))" 2>/dev/null || echo "unknown")
echo "[Hook] InstructionsLoaded: $FILE ($(date '+%Y-%m-%d %H:%M:%S'))" >> "$HOME/Desktop/업무리스트/.claude/hooks/hook_log.txt"
