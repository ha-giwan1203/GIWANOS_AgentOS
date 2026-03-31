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
echo "BLOCK (forbidden_phrase): $(grep -c 'stop_guard BLOCK.*forbidden_phrase' "$LOG")"
echo "BLOCK (missing_bucket):   $(grep -c 'stop_guard BLOCK.*missing_bucket' "$LOG")"
echo "총 BLOCK:                 $(grep -c 'stop_guard BLOCK' "$LOG")"
echo ""

# === 3. 최근 24시간 활동 ===
echo "--- 최근 활동 (마지막 20줄) ---"
tail -20 "$LOG"
echo ""

# === 4. 가장 많이 수정된 파일 Top 5 ===
echo "--- 가장 많이 수정된 파일 Top 5 ---"
grep 'PostToolUse\|protect_files' "$LOG" | grep -oE '[^ ]+\.(md|sh|json|py|xlsx)' | sort | uniq -c | sort -rn | head -5
echo ""

# === 5. 일자별 활동 추이 ===
echo "--- 일자별 활동 ---"
grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' "$LOG" | sort | uniq -c | sort -rn | head -7
echo ""

# === 6. 경고 임계치 체크 ===
echo "--- 경고 임계치 ---"
BLOCKS=$(grep -c 'stop_guard BLOCK' "$LOG" 2>/dev/null | tail -1 || echo 0)
FAILS=$(grep -c '\[FAIL\]' "$LOG" 2>/dev/null | tail -1 || echo 0)
WARNS=$(grep -c '\[WARN\]' "$LOG" 2>/dev/null | tail -1 || echo 0)

if [ "$BLOCKS" -gt 5 ]; then
  echo "[ALERT] Stop Guard BLOCK ${BLOCKS}회 — 금지 문구 반복 발생. 패턴 점검 필요"
fi
if [ "$FAILS" -gt 3 ]; then
  echo "[ALERT] 정합성 FAIL ${FAILS}회 — CLAUDE.md 내부 모순 반복. 수정 필요"
fi
if [ "$WARNS" -gt 10 ]; then
  echo "[ALERT] WARN ${WARNS}회 — 참조 파일 미존재 다수. 링크 점검 필요"
fi
if [ "$BLOCKS" -le 5 ] && [ "$FAILS" -le 3 ] && [ "$WARNS" -le 10 ]; then
  echo "모든 임계치 정상."
fi
