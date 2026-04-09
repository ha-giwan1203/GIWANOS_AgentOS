#!/usr/bin/env python3
"""unresolved incident의 다음 수리 루프를 제안한다."""

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


def infer_patch_candidates(entry: dict[str, Any]) -> list[str]:
    hook = str(entry.get("hook", ""))
    classification = str(entry.get("classification_reason", ""))
    file_field = str(entry.get("file", "")).strip()
    candidates: list[str] = []

    if file_field:
        for chunk in file_field.split(","):
            path = chunk.strip()
            if path and path not in candidates:
                candidates.append(path)

    if hook == "commit_gate":
        for path in [
            ".claude/hooks/final_check.sh",
            "90_공통기준/업무관리/TASKS.md",
            "90_공통기준/업무관리/HANDOFF.md",
        ]:
            if path not in candidates:
                candidates.append(path)
    elif hook == "completion_gate" and classification == "completion_before_git":
        for path in [
            "90_공통기준/업무관리/TASKS.md",
            "90_공통기준/업무관리/HANDOFF.md",
        ]:
            if path not in candidates:
                candidates.append(path)
    elif hook == "completion_gate" and classification == "completion_before_state_sync":
        for path in [
            "90_공통기준/업무관리/TASKS.md",
            "90_공통기준/업무관리/HANDOFF.md",
            "90_공통기준/업무관리/STATUS.md",
        ]:
            if path not in candidates:
                candidates.append(path)
    elif hook == "send_gate":
        for path in [
            ".claude/hooks/send_gate.sh",
            "90_공통기준/토론모드/ENTRY.md",
            "90_공통기준/토론모드/REFERENCE.md",
            "90_공통기준/토론모드/debate-mode/REFERENCE.md",
        ]:
            if path not in candidates:
                candidates.append(path)
    elif hook == "evidence_gate":
        for path in [
            ".claude/hooks/evidence_gate.sh",
            ".claude/hooks/evidence_mark_read.sh",
        ]:
            if path not in candidates:
                candidates.append(path)

    return candidates


def infer_verify_steps(entry: dict[str, Any]) -> list[str]:
    hook = str(entry.get("hook", ""))
    detail = str(entry.get("detail", ""))

    if hook == "commit_gate":
        mode = "--full" if "--full" in detail else "--fast"
        return [f"./.claude/hooks/final_check.sh {mode}"]
    if hook == "completion_gate":
        return [
            "./.claude/hooks/final_check.sh --fast",
            "./.claude/hooks/final_check.sh --full",
        ]
    if hook == "send_gate":
        return [
            "assistant 최신 응답 재읽기",
            "반론/대안/독립 판단 포함 후 재전송",
        ]
    if hook == "evidence_gate":
        return ["요구된 req/ok 증거 마커 충족 여부 재확인"]
    return ["관련 파일 수정 후 가장 작은 검증부터 재실행"]


def format_entry(entry: dict[str, Any]) -> str:
    lines = ["최신 unresolved incident"]
    lines.append(f"- 시각: {entry.get('ts', '')}")
    lines.append(f"- 훅: {entry.get('hook', '')}")
    lines.append(f"- 유형: {entry.get('type', '')}")
    if entry.get("file"):
        lines.append(f"- 파일: {entry.get('file', '')}")
    if entry.get("classification_reason"):
        lines.append(f"- 분류: {entry.get('classification_reason', '')}")
    lines.append(f"- 상세: {entry.get('detail', '')}")
    lines.append(f"- 다음 행동: {infer_next_action(entry)}")

    patch_candidates = infer_patch_candidates(entry)
    if patch_candidates:
        lines.append("- 패치 후보:")
        for item in patch_candidates:
            lines.append(f"  - {item}")

    verify_steps = infer_verify_steps(entry)
    if verify_steps:
        lines.append("- 검증:")
        for item in verify_steps:
            lines.append(f"  - {item}")
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
        enriched = []
        for row in selected:
            copied = dict(row)
            copied["inferred_next_action"] = infer_next_action(row)
            copied["patch_candidates"] = infer_patch_candidates(row)
            copied["verify_steps"] = infer_verify_steps(row)
            enriched.append(copied)
        print(json.dumps(enriched, ensure_ascii=False, indent=2))
        return 0

    if not selected:
        print("unresolved incident가 없습니다.")
        return 0

    if len(selected) == 1:
        print(format_entry(selected[0]))
        return 0

    print("최신 unresolved incidents")
    for entry in selected:
        print(f"- {entry.get('ts', '')} | {entry.get('hook', '')} | {infer_next_action(entry)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
