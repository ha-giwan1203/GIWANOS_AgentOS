#!/bin/bash
# ConfigChange hook — 스킬 설정 변경 감지 로그
INPUT=$(cat)
echo "[Hook] ConfigChange 감지: $(date '+%Y-%m-%d %H:%M:%S')" >> "$HOME/Desktop/업무리스트/.claude/hooks/hook_log.txt"
