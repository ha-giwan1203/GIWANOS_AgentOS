"""
Regression 자동 편입 — P1/P2 확정 실패를 smoke_test 후보로 추출.

Usage: python regression_intake.py [--dry-run]

incident_ledger.jsonl에서 true_positive/scope_violation 중 미해결 건을
smoke_test 추가 후보로 출력한다.
실제 smoke_test.sh 반영은 수동 (반자동 편입 원칙).
"""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
LEDGER = PROJECT_ROOT / ".claude" / "incident_ledger.jsonl"
SMOKE_TEST = PROJECT_ROOT / ".claude" / "hooks" / "smoke_test.sh"

# P1/P2 해당 classification_reason
P1_P2_REASONS = {"true_positive", "scope_violation"}


def load_incidents():
    if not LEDGER.exists():
        return []
    with open(LEDGER, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def filter_regression_candidates(incidents):
    """P1/P2 확정 실패 + 미해결 + 비오탐"""
    return [
        inc for inc in incidents
        if inc.get("classification_reason") in P1_P2_REASONS
        and not inc.get("resolved")
        and not inc.get("false_positive")
    ]


def generate_test_stub(inc):
    """incident에서 smoke_test 케이스 초안 생성"""
    hook = inc.get("hook", "unknown")
    reason = inc.get("classification_reason", "unknown")
    detail = inc.get("detail", "")[:80].replace('"', '\\"')
    ts = inc.get("ts", "unknown")
    return f'''# [REGRESSION] {hook} {reason} ({ts})
# Detail: {detail}
# TODO: 아래 테스트 케이스를 검증 후 주석 해제
# run_test "regression_{hook}_{reason}" \\
#   "echo test_input | bash .claude/hooks/{hook}.sh" \\
#   "expected_pattern"
'''


def main():
    dry_run = "--dry-run" in sys.argv
    incidents = load_incidents()
    candidates = filter_regression_candidates(incidents)

    if not candidates:
        print("regression 편입 후보 없음 (P1/P2 미해결 0건)")
        return

    print(f"regression 편입 후보: {len(candidates)}건")
    print()

    stubs = []
    for inc in candidates:
        stub = generate_test_stub(inc)
        stubs.append(stub)
        print(stub)

    if dry_run:
        print("[dry-run] smoke_test.sh에 추가하지 않음")
        return

    # smoke_test.sh 끝에 후보 추가 (주석 상태)
    with open(SMOKE_TEST, "a", encoding="utf-8") as f:
        f.write("\n\n# === REGRESSION CANDIDATES (auto-generated) ===\n")
        for stub in stubs:
            f.write(stub + "\n")

    print(f"\nsmoke_test.sh에 {len(stubs)}건 후보 추가 (주석 상태)")
    print("수동 확인 후 주석 해제하여 활성화하세요.")


if __name__ == "__main__":
    main()
