#!/bin/bash
# gate_boundary_check.sh — 게이트 3종 경계 재절단 회귀 트립와이어
#
# 세션91 단계 III-4 (2026-04-22) 신설. 원칙 5 "1 Problem ↔ 1 Hook".
# 성격: 회귀 트립와이어 (정합성 증명 아님). grep은 의미론 판정 불가하므로
#       "경계 침범 가능성"을 탐지하고 코드 리뷰 트리거로 사용한다.
#
# 검사 원칙 (full-line comment/blank line 제외 + 화이트리스트 주석):
#   commit_gate.sh     — TASKS/HANDOFF/STATUS 경로 grep → FAIL (상태문서 검증은 completion_gate)
#   evidence_gate.sh   — "Git diff" / "staged" 언급 grep → FAIL (Git 검증은 commit_gate)
#   completion_gate.sh — "evidence" / "근거 수집" grep → FAIL (근거 수집은 evidence_gate)
#
# 화이트리스트: 해당 라인 끝에 `# [gate-boundary-allow]` 주석 추가 시 예외 허용
#
# 근거: 90_공통기준/토론모드/logs/debate_20260422_stage3_2way/SUMMARY.md 커밋 D 섹션

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="${HOOKS_DIR:-$SCRIPT_DIR}"

FAIL=0
REPORT=""

# 검사 함수: $1=파일명, $2=grep 패턴(ERE), $3=실패 사유 prefix
check_gate() {
  local file="$1" pattern="$2" reason="$3"
  local abs="$HOOKS_DIR/$file"
  if [ ! -f "$abs" ]; then
    REPORT="${REPORT}[SKIP] $file 파일 없음\n"
    return 0
  fi
  # awk로 full-line comment(^\s*#...) + blank line 제외 + gate-boundary-allow 화이트리스트 라인 제외
  local hits
  hits=$(awk -v pat="$pattern" '
    /^[[:space:]]*#/ { next }
    /^[[:space:]]*$/ { next }
    /\[gate-boundary-allow\]/ { next }
    $0 ~ pat { printf "L%d: %s\n", NR, $0 }
  ' "$abs" 2>/dev/null)
  if [ -n "$hits" ]; then
    REPORT="${REPORT}[FAIL] $file — $reason\n$hits\n\n"
    FAIL=$((FAIL + 1))
  else
    REPORT="${REPORT}[OK] $file — $reason 경계 침범 없음\n"
  fi
}

# commit_gate.sh: 상태문서 경로 언급 금지 (완료 검증은 completion_gate 담당)
check_gate "commit_gate.sh" 'TASKS\.md|HANDOFF\.md|STATUS\.md' "TASKS/HANDOFF/STATUS 경로"

# evidence_gate.sh: Git diff/staged 언급 금지 (Git 검증은 commit_gate 담당)
check_gate "evidence_gate.sh" 'git diff|--cached|staged' "Git diff/staged"

# completion_gate.sh: evidence/근거 수집 언급 금지 (근거 수집은 evidence_gate 담당)
check_gate "completion_gate.sh" '\.req|근거 수집|fresh_req|fresh_ok' "evidence/근거 수집"

printf "%b" "$REPORT"
if [ "$FAIL" -gt 0 ]; then
  echo ""
  echo "=== gate_boundary_check: FAIL $FAIL 건 ==="
  exit 1
fi
echo ""
echo "=== gate_boundary_check: ALL PASS ==="
exit 0
