#!/bin/bash
# hook_log.txt 분석 스크립트 — hook KPI 산출
# 용도: 운영 검증 체계. 차단 횟수, 경고 수, 파일별 빈도 등 집계

LOG="$HOME/Desktop/업무리스트/.claude/hooks/hook_log.txt"

if [ ! -f "$LOG" ]; then
  echo "hook_log.txt 없음"
  exit 1
fi

TOTAL=$(wc -l < "$LOG")
echo "=== Hook KPI Report ==="
echo "총 로그: ${TOTAL}줄"
echo ""

# === 1. Hook 유형별 빈도 ===
echo "--- Hook 유형별 빈도 ---"
echo "PreToolUse (protect_files): $(grep -c 'protect_files' "$LOG")"
echo "PostToolUse:                $(grep -c 'PostToolUse' "$LOG")"
echo "CLAUDE.md 수정 감지:       $(grep -c 'CLAUDE.md 수정 감지' "$LOG")"
echo "TASKS.md 수정 감지:        $(grep -c 'TASKS.md 수정 감지' "$LOG")"
echo "git commit 감지:           $(grep -c 'git commit 감지' "$LOG")"
echo "정합성 검사 PASS:          $(grep -c '정합성 검사 PASS' "$LOG")"
echo "정합성 검사 FAIL:          $(grep -c '\[FAIL\]' "$LOG")"
echo "정합성 검사 WARN:          $(grep -c '\[WARN\]' "$LOG")"
echo ""

# === 2. Stop Guard 차단 (별도 로그가 없으면 transcript 기반) ===
echo "--- Stop Guard ---"
echo "Stop Guard는 transcript에서 exit 2로 차단하므로 hook_log.txt에 기록 안 됨."
echo "실전 차단 횟수는 다음 세션에서 transcript 분석으로 확인 필요."
echo ""

# === 3. 최근 24시간 활동 ===
echo "--- 최근 활동 (마지막 20줄) ---"
tail -20 "$LOG"
echo ""

# === 4. 가장 많이 수정된 파일 Top 5 ===
echo "--- 가장 많이 수정된 파일 Top 5 ---"
grep 'PostToolUse\|protect_files' "$LOG" | grep -oE '[^ ]+\.(md|sh|json|py|xlsx)' | sort | uniq -c | sort -rn | head -5
