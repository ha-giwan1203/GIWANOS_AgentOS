#!/bin/bash
# Fast Smoke Subset — SessionStart 시 자동 실행 (5~8건, 로컬·결정적만)
# 네트워크/외부 API 검사 없음. 실패 시 경고만 (차단 아님)
# Full smoke test: smoke_test.sh (105건)

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
HOOKS_DIR="$PROJECT_DIR/.claude/hooks"
SETTINGS_TEAM="$PROJECT_DIR/.claude/settings.json"
SETTINGS_LOCAL="$PROJECT_DIR/.claude/settings.local.json"

PASS=0
FAIL=0
TOTAL=0

check() {
  TOTAL=$((TOTAL+1))
  if [ "$1" = "0" ]; then
    PASS=$((PASS+1))
  else
    FAIL=$((FAIL+1))
    echo "  [FAST-FAIL] $2"
  fi
}

# 1. hook_common.sh 존재 + 핵심 함수
test -f "$HOOKS_DIR/hook_common.sh"
check $? "hook_common.sh 존재"

grep -q 'hook_log()' "$HOOKS_DIR/hook_common.sh"
check $? "hook_log() 함수 존재"

# 2. settings JSON 유효성 — team+local 양쪽 모두
PY_CMD="python"; command -v python3 >/dev/null 2>&1 && PY_CMD="python3"
if [ -f "$SETTINGS_TEAM" ]; then
  $PY_CMD -c "import json,sys; json.load(open(sys.argv[1], encoding='utf-8'))" "$SETTINGS_TEAM" 2>/dev/null
  check $? "settings.json 유효 JSON"
fi
$PY_CMD -c "import json,sys; json.load(open(sys.argv[1], encoding='utf-8'))" "$SETTINGS_LOCAL" 2>/dev/null
check $? "settings.local.json 유효 JSON"

# 3. 핵심 게이트 훅 존재 + 실행 가능
for hook in commit_gate.sh mcp_send_gate.sh completion_gate.sh evidence_gate.sh; do
  test -x "$HOOKS_DIR/$hook"
  check $? "$hook 존재+실행가능"
done

# 4. TASKS.md / HANDOFF.md 존재
test -f "$PROJECT_DIR/90_공통기준/업무관리/TASKS.md"
check $? "TASKS.md 존재"

test -f "$PROJECT_DIR/90_공통기준/업무관리/HANDOFF.md"
check $? "HANDOFF.md 존재"

# 5. gate_boundary_check — 게이트 3종 경계 재절단 회귀 트립와이어 (세션91 단계 III-4)
bash "$HOOKS_DIR/gate_boundary_check.sh" >/dev/null 2>&1
check $? "gate_boundary_check PASS"

# 결과 출력
if [ "$FAIL" -gt 0 ]; then
  echo "[smoke_fast] $PASS/$TOTAL PASS, $FAIL FAIL — 세션 시작 전 확인 필요"
else
  echo "[smoke_fast] $PASS/$TOTAL ALL PASS"
fi

exit 0
