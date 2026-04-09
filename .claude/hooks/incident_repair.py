#!/usr/bin/env python3
"""Suggest next repair actions for unresolved incidents."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def infer_next_action(entry: dict[str, Any]) -> str:
    hinted = entry.get("next_action")
    if isinstance(hinted, str) and hinted.strip():
        return hinted.strip()

    hook = str(entry.get("hook", ""))
    detail = str(entry.get("detail", ""))

    if hook == "commit_gate":
        mode = "--full" if "--full" in detail else "--fast"
        return f"./.claude/hooks/final_check.sh {mode} 를 다시 실행해 FAIL 항목부터 정리"
    if hook == "completion_gate" and "Git" in detail:
        return "relevant change를 commit/push 또는 정리한 뒤 완료 보고 재시도"
    if hook == "completion_gate" and ("TASKS" in detail or "HANDOFF" in detail):
        return "TASKS/HANDOFF를 최신 작업 상태로 갱신한 뒤 완료 보고 재시도"
    if hook == "send_gate":
        return "assistant 최신 응답을 다시 읽고 반론/대안/독립 판단을 넣어 재전송"
    if hook == "date_scope_guard":
        return "YYYY-MM-DD 절대날짜와 요일을 확인한 뒤 다시 실행"
    if hook == "evidence_gate":
        return "해당 req/ok 증거 마커를 먼저 충족한 뒤 재시도"
    return "최근 로그와 관련 파일을 읽고 원인 확인 후 가장 작은 수정부터 재시도"


def format_entry(entry: dict[str, Any]) -> str:
    lines = ["Latest unresolved incident"]
    lines.append(f"- ts: {entry.get('ts', '')}")
    lines.append(f"- hook: {entry.get('hook', '')}")
    lines.append(f"- type: {entry.get('type', '')}")
    if entry.get("file"):
        lines.append(f"- file: {entry.get('file', '')}")
    if entry.get("classification_reason"):
        lines.append(f"- classification: {entry.get('classification_reason', '')}")
    lines.append(f"- detail: {entry.get('detail', '')}")
    lines.append(f"- next action: {infer_next_action(entry)}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Suggest next repair actions for unresolved incidents.")
    parser.add_argument(
        "--ledger",
        default=".claude/incident_ledger.jsonl",
        help="incident ledger path (default: .claude/incident_ledger.jsonl)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="number of latest unresolved incidents to show (default: 1)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print selected incidents as JSON",
    )
    args = parser.parse_args()

    entries = load_jsonl(Path(args.ledger))
    unresolved = [row for row in entries if not row.get("resolved", False)]
    selected = unresolved[-max(args.limit, 1) :]

    if args.json:
        print(json.dumps(selected, ensure_ascii=False, indent=2))
        return 0

    if not selected:
        print("No unresolved incidents.")
        return 0

    if len(selected) == 1:
        print(format_entry(selected[0]))
        return 0

    print("Latest unresolved incidents")
    for entry in selected:
        print(f"- {entry.get('ts', '')} | {entry.get('hook', '')} | {infer_next_action(entry)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
