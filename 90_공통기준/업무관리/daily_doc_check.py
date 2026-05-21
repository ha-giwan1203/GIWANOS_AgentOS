"""
daily_doc_check.py — TASKS/STATUS/HANDOFF 정합성 자동 판정

목적: Claude의 grep+Read 인지 의존 제거. 스크립트가 직접 PASS/FAIL 판정해서 출력.
SKILL.md(daily-doc-check)에서 호출.

판정 기준 (SKILL.md와 동일):
1. TASKS 진행중 항목 > 1: FAIL (`[작업중] owner=...` 잠금 포함)
2. STATUS 세션 < TASKS 세션 (1세션 이상 drift): FAIL
3. HANDOFF에 `## [완료/진행/...]` 또는 `^상태:`/`^판정:` 독립 선언: FAIL

사용법:
    python daily_doc_check.py              # 판정만 출력 (exit 0=PASS / 1=FAIL)
    python daily_doc_check.py --slack      # FAIL 시 Slack 알림 동시 발송
    python daily_doc_check.py --json       # 결과를 JSON으로 출력
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Windows cp949 콘솔에서도 한글·이모지 출력 가능하도록 utf-8 강제
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # 업무리스트 루트
TASKS = REPO_ROOT / "90_공통기준" / "업무관리" / "TASKS.md"
STATUS = REPO_ROOT / "90_공통기준" / "업무관리" / "STATUS.md"
HANDOFF = REPO_ROOT / "90_공통기준" / "업무관리" / "HANDOFF.md"
SLACK_NOTIFY = REPO_ROOT / "90_공통기준" / "업무관리" / "slack_notify.py"

SESSION_RE = re.compile(r"세션(\d+)")
IN_PROGRESS_HEADER_RE = re.compile(r"^### \[진행중?\]", re.MULTILINE)
IN_PROGRESS_CHECKBOX_RE = re.compile(r"^- \[ \]", re.MULTILINE)
CODEX_IN_PROGRESS_RE = re.compile(r"^- \[작업중\]\s+owner=", re.MULTILINE)
HANDOFF_FORBIDDEN_HEADER_RE = re.compile(r"^## \[(완료|진행|보류|차단)\]", re.MULTILINE)
HANDOFF_FORBIDDEN_STATUS_RE = re.compile(r"^(상태|판정)[:：]", re.MULTILINE)


def extract_session(path: Path) -> int | None:
    """파일 상단 50줄에서 첫 세션 번호 추출. 못 찾으면 None."""
    if not path.exists():
        return None
    head = "".join(path.open(encoding="utf-8").readlines()[:50])
    m = SESSION_RE.search(head)
    return int(m.group(1)) if m else None


def count_in_progress(path: Path) -> int:
    """TASKS.md에서 [진행중] 헤더 + Codex 작업잠금 + 미완료 체크박스 합계."""
    if not path.exists():
        return 0
    txt = path.read_text(encoding="utf-8")
    # 헤더 안내문(L4) 제외 — `완료/미완료/진행중/차단` 같은 메타 설명
    txt = re.sub(r"^> .*$", "", txt, flags=re.MULTILINE)
    headers = len(IN_PROGRESS_HEADER_RE.findall(txt))
    codex_locks = len(CODEX_IN_PROGRESS_RE.findall(txt))
    checkboxes = len(IN_PROGRESS_CHECKBOX_RE.findall(txt))
    return headers + codex_locks + checkboxes


def detect_handoff_forbidden(path: Path) -> list[str]:
    """HANDOFF.md 독립 상태 선언 라인 추출. 안내문(`>` 블록)은 제외."""
    if not path.exists():
        return []
    txt = path.read_text(encoding="utf-8")
    # `>` 인용 블록(안내문) 제외
    txt = re.sub(r"^> .*$", "", txt, flags=re.MULTILINE)
    hits = []
    for m in HANDOFF_FORBIDDEN_HEADER_RE.finditer(txt):
        hits.append(m.group(0))
    for m in HANDOFF_FORBIDDEN_STATUS_RE.finditer(txt):
        hits.append(m.group(0))
    return hits


def judge() -> dict:
    """3개 항목 판정 후 결과 dict 반환."""
    tasks_session = extract_session(TASKS)
    status_session = extract_session(STATUS)
    handoff_session = extract_session(HANDOFF)
    in_progress = count_in_progress(TASKS)
    handoff_forbidden = detect_handoff_forbidden(HANDOFF)

    checks = {
        "in_progress": {
            "value": in_progress,
            "threshold": 1,
            "pass": in_progress <= 1,
            "label": "TASKS 진행중 항목 ≤ 1",
        },
        "status_session": {
            "tasks": tasks_session,
            "status": status_session,
            "pass": (
                tasks_session is not None
                and status_session is not None
                and status_session >= tasks_session
            ),
            "label": "STATUS 세션 ≥ TASKS 세션",
        },
        "handoff_declarations": {
            "hits": handoff_forbidden,
            "pass": len(handoff_forbidden) == 0,
            "label": "HANDOFF 독립 상태 선언 없음",
        },
    }
    all_pass = all(c["pass"] for c in checks.values())

    return {
        "overall": "PASS" if all_pass else "FAIL",
        "tasks_session": tasks_session,
        "status_session": status_session,
        "handoff_session": handoff_session,
        "checks": checks,
    }


def format_table(result: dict) -> str:
    """비개발자도 읽을 수 있는 표 형식 출력."""
    lines = []
    lines.append(f"## 일일 문서 정합성 점검 — {result['overall']}")
    lines.append("")
    lines.append("| 점검 항목 | 결과 | 값 |")
    lines.append("|----------|------|-----|")
    for key, c in result["checks"].items():
        mark = "✅ PASS" if c["pass"] else "❌ FAIL"
        if key == "in_progress":
            val = f"{c['value']}건"
        elif key == "status_session":
            val = f"TASKS=세션{c['tasks']} / STATUS=세션{c['status']}"
        else:
            val = f"{len(c['hits'])}건" + (
                f" ({', '.join(c['hits'][:3])}{'...' if len(c['hits']) > 3 else ''})"
                if c["hits"]
                else ""
            )
        lines.append(f"| {c['label']} | {mark} | {val} |")
    lines.append("")
    lines.append(
        f"세션 번호 — TASKS:{result['tasks_session']} / "
        f"STATUS:{result['status_session']} / HANDOFF:{result['handoff_session']}"
    )
    # FAIL 아닌 warn: HANDOFF 세션이 TASKS보다 뒤처짐 (본문은 사람이 갱신 — 자동 fix 대상 아님)
    ts, hs = result["tasks_session"], result["handoff_session"]
    if ts is not None and hs is not None and hs < ts:
        lines.append("")
        lines.append(
            f"⚠️ HANDOFF 세션({hs}) < TASKS 세션({ts}) — 인수인계 메모 갱신 필요 "
            "(자동 fix 대상 아님: 본문이 사람이 쓰는 인수인계 영역)"
        )
    return "\n".join(lines)


def send_slack(message: str) -> bool:
    """slack_notify.py --message 호출."""
    if not SLACK_NOTIFY.exists():
        print(f"[WARN] slack_notify.py 없음: {SLACK_NOTIFY}", file=sys.stderr)
        return False
    try:
        r = subprocess.run(
            [sys.executable, str(SLACK_NOTIFY), "--message", message],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
        )
        print(r.stdout, end="")
        if r.returncode != 0:
            print(r.stderr, file=sys.stderr, end="")
            return False
        return "성공" in (r.stdout or "")
    except Exception as e:
        print(f"[ERR] Slack 호출 실패: {e}", file=sys.stderr)
        return False


def main():
    ap = argparse.ArgumentParser(description="TASKS/STATUS/HANDOFF 정합성 자동 판정")
    ap.add_argument("--slack", action="store_true", help="FAIL 시 Slack 알림 발송")
    ap.add_argument("--json", action="store_true", help="결과를 JSON으로 출력")
    args = ap.parse_args()

    result = judge()

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_table(result))

    if result["overall"] == "FAIL" and args.slack:
        msg = format_table(result) + "\n\n권고: TASKS/STATUS/HANDOFF 세션 라벨 동기화 + HANDOFF 독립 선언 제거"
        ok = send_slack(msg)
        print(f"\nSlack 발송: {'성공' if ok else '실패'}", file=sys.stderr)

    sys.exit(0 if result["overall"] == "PASS" else 1)


if __name__ == "__main__":
    main()
