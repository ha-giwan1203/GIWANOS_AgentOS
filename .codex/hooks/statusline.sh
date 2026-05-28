#!/bin/bash
# statusline — Claude Code 상태 표시줄
# 입력: JSON (stdin) — {model:{display_name,id}, workspace:{current_dir,project_dir}, cost:{total_cost_usd}}
# 출력: 첫 줄만 표시됨
# 2026-04-18 3자 토론 합의안 (우선순위 4)
# 세션93 (2026-04-22 auto-fix A-2): python3 하드의존 → PY_CMD fallback

PY_CMD="python"; command -v python3 >/dev/null 2>&1 && PY_CMD="python3"

# 2026-04-20 3자 토론 합의안: heredoc 인라인 삽입 패턴(json.loads('''$input''')) 제거 →
# stdin 파이프(json.load(sys.stdin))로 전달. 입력 escape 문제 근본 해소.
parsed=$(cat | PYTHONIOENCODING=utf-8 PYTHONUTF8=1 "$PY_CMD" <<'PY' 2>/dev/null
import json, sys, os
try:
    d = json.load(sys.stdin)
    model = d.get('model', {}).get('display_name', 'claude')
    cwd = d.get('workspace', {}).get('current_dir', os.getcwd())
    cwd_short = os.path.basename(cwd.rstrip('/').rstrip('\\'))
    cost = d.get('cost', {}).get('total_cost_usd', 0)
    print(f"{model}|{cwd_short}|{cost:.2f}")
except Exception:
    print("claude|?|0.00")
PY
)

IFS='|' read -r MODEL CWD COST <<< "$parsed"

# Git 브랜치
BRANCH=$(git branch --show-current 2>/dev/null || echo "-")

# 컬러 ANSI (터미널이 지원하는 경우)
C_RESET=$'\033[0m'
C_CYAN=$'\033[36m'
C_GREEN=$'\033[32m'
C_YELLOW=$'\033[33m'
C_DIM=$'\033[2m'

echo "${C_CYAN}${MODEL}${C_RESET} ${C_DIM}|${C_RESET} ${C_GREEN}${CWD}${C_RESET} ${C_DIM}(${BRANCH})${C_RESET} ${C_DIM}|${C_RESET} ${C_YELLOW}\$${COST}${C_RESET}"
