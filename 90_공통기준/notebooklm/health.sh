#!/usr/bin/env bash
# NotebookLM 컨트롤 레이어 헬스 점검
#
# 출력:
#   - registry.yaml 존재 / 노트북 개수 / active 개수
#   - 도메인 에이전트 존재 여부
#   - 슬래시 커맨드 등록 여부
#
# MCP 인증 상태(authenticated)는 sh로 확인 불가 — Claude가 mcp__notebooklm-mcp__get_health 직접 호출.
# 이 스크립트는 정적 자산 점검만 수행.

set -u
cd "$(dirname "$0")/../.." || exit 1
ROOT="$(pwd)"

REG="$ROOT/90_공통기준/notebooklm/registry.yaml"
BRIDGE="$ROOT/90_공통기준/notebooklm/bridge.md"
CMD="$ROOT/.claude/commands/notebooklm.md"
AGENT_LB="$ROOT/.claude/agents/line-batch-domain-expert.md"
AGENT_ST="$ROOT/.claude/agents/settlement-domain-expert.md"

PASS=0
FAIL=0
WARN=0

check() {
  local label="$1"
  local path="$2"
  local req="$3"   # required | optional
  if [ -f "$path" ]; then
    echo "  [OK] $label  ($path)"
    PASS=$((PASS+1))
  else
    if [ "$req" = "required" ]; then
      echo "  [FAIL] $label  (없음: $path)"
      FAIL=$((FAIL+1))
    else
      echo "  [WARN] $label  (선택 자산 없음: $path)"
      WARN=$((WARN+1))
    fi
  fi
}

echo "=== NotebookLM 컨트롤 레이어 헬스 ==="
echo

echo "[정적 자산]"
check "registry.yaml"         "$REG"       required
check "bridge.md"             "$BRIDGE"    required
check "/notebooklm 슬래시"    "$CMD"       required
check "line-batch 에이전트"   "$AGENT_LB"  optional
check "settlement 에이전트"   "$AGENT_ST"  optional

echo
echo "[registry.yaml 요약]"
if [ -f "$REG" ]; then
  TOTAL=$(grep -cE '^\s*-\s*name:' "$REG" || echo 0)
  ACTIVE=$(grep -cE '^\s*active:\s*true' "$REG" || echo 0)
  echo "  등록 노트북: $TOTAL건"
  echo "  활성 노트북: $ACTIVE건"
  echo "  도메인 목록:"
  grep -E '^\s*domain:' "$REG" | sed 's/^/    /'
fi

echo
echo "[다음 단계 — Claude가 실행]"
echo "  1. mcp__notebooklm-mcp__get_health  → authenticated 확인"
echo "  2. 미인증 시: mcp__notebooklm-mcp__setup_auth"
echo "  3. mcp__notebooklm-mcp__list_notebooks  → registry와 대조"
echo

echo "=== 결과: PASS=$PASS  WARN=$WARN  FAIL=$FAIL ==="
[ "$FAIL" -eq 0 ]
