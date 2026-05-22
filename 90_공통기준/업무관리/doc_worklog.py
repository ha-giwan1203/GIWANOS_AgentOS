"""
doc_worklog.py — TASKS/HANDOFF/STATUS 갱신 전용 도구

목적: 작업 상태 문서를 직접 편집하다가 완료줄 위치, HANDOFF 위치,
STATUS 세션 갱신을 반복 실수하는 문제를 줄인다.

사용 예:
    python doc_worklog.py start --task "작업명" --paths "a.md" ^
        --harness-input "요청/기준" --harness-scope "수정 범위" ^
        --harness-success "성공 기준" --harness-verify "검증 명령" ^
        --harness-stop "중단 기준"
    python doc_worklog.py complete --task "작업명" --paths "a.md" "b.py" ^
        --handoff "완료 내용 1단락" --status-title "작업 완료"
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TASKS = REPO_ROOT / "90_공통기준" / "업무관리" / "TASKS.md"
HANDOFF = REPO_ROOT / "90_공통기준" / "업무관리" / "HANDOFF.md"
STATUS = REPO_ROOT / "90_공통기준" / "업무관리" / "STATUS.md"

STATUS_SESSION_RE = re.compile(r"세션(\d+)")
STATUS_UPDATE_RE = re.compile(r"^최종 업데이트: .*$")
TASK_START_PREFIX = "- [작업중] owner=Codex / "
TASK_DONE_PREFIX = "- [완료] owner=Codex / "
HARNESS_FIELDS = [
    ("input", "입력"),
    ("scope", "범위"),
    ("success", "성공"),
    ("verify", "검증"),
    ("stop", "중단"),
]


def read_lines(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8").lstrip("\ufeff")
    return text.splitlines()


def write_lines(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def paths_text(paths: list[str]) -> str:
    return ", ".join(f"`{p}`" for p in paths)


def harness_text(harness: dict[str, str] | None) -> str:
    if not harness:
        return ""
    parts = [f"{label}={harness[key]}" for key, label in HARNESS_FIELDS]
    return " / 하네스: " + "; ".join(parts)


def task_line(state: str, task: str, paths: list[str], harness: dict[str, str] | None = None) -> str:
    if state == "start":
        return f"{TASK_START_PREFIX}{task} / 잠금 파일: {paths_text(paths)}{harness_text(harness)}"
    if state == "done":
        return f"{TASK_DONE_PREFIX}{task} / 잠금 해제: {paths_text(paths)}"
    raise ValueError(f"unknown state: {state}")


def insert_top_task_line(line: str) -> None:
    lines = read_lines(TASKS)
    if line in lines:
        raise SystemExit(f"[FAIL] TASKS에 같은 줄이 이미 있습니다: {line}")
    lines.insert(0, line)
    write_lines(TASKS, lines)


def complete_task_line(task: str, paths: list[str]) -> None:
    lines = read_lines(TASKS)
    start_prefix = f"{TASK_START_PREFIX}{task} / "
    done = task_line("done", task, paths)
    replaced = False

    for i, line in enumerate(lines):
        if line.startswith(start_prefix):
            lines[i] = done
            replaced = True
            break

    if not replaced:
        if done in lines:
            return
        lines.insert(0, done)

    # 같은 완료줄이 아래에 중복으로 붙는 실수를 방지한다.
    deduped: list[str] = []
    seen_done = False
    for line in lines:
        if line == done:
            if seen_done:
                continue
            seen_done = True
        deduped.append(line)
    write_lines(TASKS, deduped)


def next_session() -> int:
    head = "\n".join(read_lines(STATUS)[:20])
    match = STATUS_SESSION_RE.search(head)
    if not match:
        raise SystemExit("[FAIL] STATUS 상단에서 세션 번호를 찾지 못했습니다.")
    return int(match.group(1)) + 1


def update_status(session: int, status_title: str) -> None:
    lines = read_lines(STATUS)
    new_line = f"최종 업데이트: {datetime.now():%Y-%m-%d} KST — 세션{session} ({status_title})"
    for i, line in enumerate(lines):
        if STATUS_UPDATE_RE.match(line):
            lines[i] = new_line
            write_lines(STATUS, lines)
            return
    raise SystemExit("[FAIL] STATUS 최종 업데이트 줄을 찾지 못했습니다.")


def handoff_insert_index(lines: list[str]) -> int:
    # 제목 + 안내 인용문 직후 첫 본문 위치에 최신 메모를 넣는다.
    for i, line in enumerate(lines):
        if line.startswith("최종 업데이트:"):
            return i
    return len(lines)


def insert_handoff(handoff_text: str) -> None:
    lines = read_lines(HANDOFF)
    paragraph = f"최종 업데이트: {datetime.now():%Y-%m-%d} KST — **Codex** {handoff_text}"
    idx = handoff_insert_index(lines)
    insert_block = [paragraph, ""]
    lines[idx:idx] = insert_block
    write_lines(HANDOFF, lines)


def build_harness(args: argparse.Namespace) -> dict[str, str] | None:
    values = {
        "input": args.harness_input,
        "scope": args.harness_scope,
        "success": args.harness_success,
        "verify": args.harness_verify,
        "stop": args.harness_stop,
    }
    present = {key: bool(value) for key, value in values.items()}
    if not any(present.values()):
        raise SystemExit("[FAIL] Codex 작업 시작에는 하네스 5필드가 필요합니다.")
    if not all(present.values()):
        missing = ", ".join(label for key, label in HARNESS_FIELDS if not present[key])
        raise SystemExit(f"[FAIL] 하네스 5필드가 모두 필요합니다. 누락: {missing}")
    return values


def start(args: argparse.Namespace) -> None:
    insert_top_task_line(task_line("start", args.task, args.paths, build_harness(args)))
    print("[OK] TASKS 작업중 줄을 상단에 추가했습니다.")


def complete(args: argparse.Namespace) -> None:
    session = args.session if args.session is not None else next_session()
    complete_task_line(args.task, args.paths)
    insert_handoff(args.handoff)
    update_status(session, args.status_title)
    print(f"[OK] 문서 갱신 완료: 세션{session}")


def main() -> None:
    parser = argparse.ArgumentParser(description="TASKS/HANDOFF/STATUS 갱신 전용 도구")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_start = sub.add_parser("start", help="TASKS 상단에 작업중 줄 추가")
    p_start.add_argument("--task", required=True, help="작업명")
    p_start.add_argument("--paths", nargs="+", required=True, help="잠금 파일/폴더")
    p_start.add_argument("--harness-input", help="작업 전용 하네스 입력 기준")
    p_start.add_argument("--harness-scope", help="작업 전용 하네스 작업 범위")
    p_start.add_argument("--harness-success", help="작업 전용 하네스 성공 기준")
    p_start.add_argument("--harness-verify", help="작업 전용 하네스 검증 명령")
    p_start.add_argument("--harness-stop", help="작업 전용 하네스 중단 기준")
    p_start.set_defaults(func=start)

    p_complete = sub.add_parser("complete", help="TASKS 완료 + HANDOFF + STATUS 갱신")
    p_complete.add_argument("--task", required=True, help="작업명")
    p_complete.add_argument("--paths", nargs="+", required=True, help="잠금 해제 파일/폴더")
    p_complete.add_argument("--handoff", required=True, help="HANDOFF에 넣을 1단락")
    p_complete.add_argument("--status-title", required=True, help="STATUS 최종 업데이트 괄호 제목")
    p_complete.add_argument("--session", type=int, help="세션 번호. 생략 시 STATUS+1")
    p_complete.set_defaults(func=complete)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
