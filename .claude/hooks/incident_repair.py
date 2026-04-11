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

    reason = str(entry.get("classification_reason", ""))
    hook = str(entry.get("hook", ""))
    detail = str(entry.get("detail", ""))

    # classification_reason 기반 (세션12 enum 표준화)
    actions: dict[str, str] = {
        "evidence_missing": "해당 req/ok 증거 마커를 먼저 충족한 뒤 재시도",
        "completion_before_git": "relevant change를 commit/push 또는 정리한 뒤 완료 보고 재시도",
        "completion_before_state_sync": "TASKS/HANDOFF를 최신 작업 상태로 갱신한 뒤 완료 보고 재시도",
        "pre_commit_check": "./.claude/hooks/final_check.sh --fast 를 다시 실행해 FAIL 항목부터 정리",
        "scope_violation": "YYYY-MM-DD 절대날짜와 요일을 확인한 뒤 다시 실행",
        "dangerous_cmd": "사용자 직접 실행 또는 안전한 대안 명령 사용",
        "send_block": "CDP 기본 경로(cdp_chat_send.py)로 전환하여 재전송",
        "stop_guard_block": "독립 견해(반론/대안/내 판단)를 포함하여 재작성",
        "compile_fail": "문법 오류를 수정한 뒤 py_compile로 재검증",
    }
    if reason in actions:
        return actions[reason]

    # fallback: hook 기반 (레거시 데이터 호환)
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
    if hook == "evidence_gate" or hook == "evidence_stop_guard":
        return "해당 req/ok 증거 마커를 먼저 충족한 뒤 재시도"
    if hook == "block_dangerous":
        return "사용자 직접 실행 또는 안전한 대안 명령 사용"
    if hook == "stop_guard":
        return "독립 견해(반론/대안/내 판단)를 포함하여 재작성"
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

    # classification_reason 기반 매핑 (세션12 표준화)
    reason_paths: dict[str, list[str]] = {
        "pre_commit_check": [
            ".claude/hooks/final_check.sh",
            "90_공통기준/업무관리/TASKS.md",
            "90_공통기준/업무관리/HANDOFF.md",
        ],
        "completion_before_git": [
            "90_공통기준/업무관리/TASKS.md",
            "90_공통기준/업무관리/HANDOFF.md",
        ],
        "completion_before_state_sync": [
            "90_공통기준/업무관리/TASKS.md",
            "90_공통기준/업무관리/HANDOFF.md",
            "90_공통기준/업무관리/STATUS.md",
        ],
        "evidence_missing": [
            ".claude/hooks/evidence_gate.sh",
            ".claude/hooks/evidence_mark_read.sh",
        ],
        "send_block": [
            ".claude/hooks/send_gate.sh",
            "90_공통기준/토론모드/ENTRY.md",
        ],
        "scope_violation": [],
        "dangerous_cmd": [],
        "stop_guard_block": [],
        "compile_fail": [],
    }

    if classification in reason_paths:
        for path in reason_paths[classification]:
            if path not in candidates:
                candidates.append(path)
    else:
        # fallback: hook 기반 (레거시)
        hook_paths: dict[str, list[str]] = {
            "commit_gate": reason_paths["pre_commit_check"],
            "completion_gate": reason_paths.get(
                "completion_before_state_sync",
                reason_paths["completion_before_git"],
            ),
            "send_gate": reason_paths["send_block"],
            "evidence_gate": reason_paths["evidence_missing"],
            "evidence_stop_guard": reason_paths["evidence_missing"],
        }
        for path in hook_paths.get(hook, []):
            if path not in candidates:
                candidates.append(path)

    return candidates


def infer_verify_steps(entry: dict[str, Any]) -> list[str]:
    reason = str(entry.get("classification_reason", ""))
    hook = str(entry.get("hook", ""))
    detail = str(entry.get("detail", ""))

    # classification_reason 기반 (세션12 표준화)
    reason_steps: dict[str, list[str]] = {
        "pre_commit_check": ["./.claude/hooks/final_check.sh --fast"],
        "completion_before_git": ["git status로 미커밋 변경 확인", "git add + commit + push"],
        "completion_before_state_sync": [
            "./.claude/hooks/final_check.sh --fast",
            "TASKS.md / HANDOFF.md 갱신 확인",
        ],
        "evidence_missing": ["요구된 req/ok 증거 마커 충족 여부 재확인"],
        "scope_violation": ["date 명령으로 현재 날짜/요일 확인"],
        "dangerous_cmd": ["사용자에게 직접 실행 안내"],
        "send_block": ["cdp_chat_send.py 경로로 재전송"],
        "stop_guard_block": ["반론/대안/독립 판단 포함 여부 재확인"],
        "compile_fail": ["python -m py_compile <file> 재실행"],
    }
    if reason in reason_steps:
        return reason_steps[reason]

    # fallback: hook 기반
    if hook == "commit_gate":
        mode = "--full" if "--full" in detail else "--fast"
        return [f"./.claude/hooks/final_check.sh {mode}"]
    if hook == "completion_gate":
        return ["./.claude/hooks/final_check.sh --fast"]
    if hook == "send_gate":
        return ["cdp_chat_send.py 경로로 재전송"]
    if hook in ("evidence_gate", "evidence_stop_guard"):
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


def auto_resolve(ledger_path: Path, dry_run: bool = False) -> int:
    """규칙 명확한 incident를 자동 resolved 마킹.

    자동 해소 대상 (세션12 GPT+Claude 합의):
    - evidence_missing: 24시간 경과 시 (세션 간 증거 비교 복잡하므로 시간 기반)
    - pre_commit_check: 24시간 경과 시 (후속 커밋 성공 추적 대신 시간 기반)
    - scope_violation: 24시간 경과 시 (1회성 차단)
    - dangerous_cmd: 24시간 경과 시 (1회성 차단)

    방식: resolved=false → resolved=true + resolved_by="auto" 로 덮어쓰기
    """
    import datetime

    entries = load_jsonl(ledger_path)
    now = datetime.datetime.now(datetime.timezone.utc)
    count = 0

    for entry in entries:
        if entry.get("resolved"):
            continue
        reason = str(entry.get("classification_reason", ""))
        hook = str(entry.get("hook", ""))

        should_resolve = False

        # scope_violation / dangerous_cmd: 1회성 차단, 24시간 경과 시 자동 해소
        if reason in ("scope_violation", "dangerous_cmd") or hook in ("date_scope_guard", "block_dangerous"):
            ts_str = entry.get("ts", "")
            try:
                ts = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if (now - ts).total_seconds() > 86400:
                    should_resolve = True
            except (ValueError, TypeError):
                pass

        # evidence_missing: 24시간 경과 시 자동 해소 (세션 간 증거 비교 복잡하므로 시간 기반)
        if reason == "evidence_missing" or hook in ("evidence_gate", "evidence_stop_guard"):
            ts_str = entry.get("ts", "")
            try:
                ts = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if (now - ts).total_seconds() > 86400:
                    should_resolve = True
            except (ValueError, TypeError):
                pass

        # pre_commit_check: 24시간 경과 시 자동 해소
        if reason == "pre_commit_check" or (hook == "commit_gate" and reason != "structural_intermediate"):
            ts_str = entry.get("ts", "")
            try:
                ts = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if (now - ts).total_seconds() > 86400:
                    should_resolve = True
            except (ValueError, TypeError):
                pass

        if should_resolve:
            entry["resolved"] = True
            entry["resolved_by"] = "auto"
            count += 1

    if not dry_run and count > 0:
        with ledger_path.open("w", encoding="utf-8") as fh:
            for entry in entries:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return count


def archive_resolved(ledger_path: Path, days: int = 30, dry_run: bool = False) -> int:
    """resolved=true이고 days일 경과한 항목을 아카이브 파일로 이동.

    GPT+Claude 합의 2026-04-11: ledger 무한 성장 억제.
    감사 원본은 개별 시점 정보를 보존하되, 오래된 resolved 항목은
    별도 아카이브로 분리하여 활성 ledger를 경량화한다.
    """
    import datetime

    entries = load_jsonl(ledger_path)
    now = datetime.datetime.now(datetime.timezone.utc)
    threshold_seconds = days * 86400

    keep: list[dict[str, Any]] = []
    archive: list[dict[str, Any]] = []

    for entry in entries:
        if not entry.get("resolved"):
            keep.append(entry)
            continue
        ts_str = entry.get("ts", "")
        try:
            ts = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if (now - ts).total_seconds() > threshold_seconds:
                archive.append(entry)
            else:
                keep.append(entry)
        except (ValueError, TypeError):
            keep.append(entry)  # 파싱 실패 시 보존

    if not dry_run and archive:
        archive_path = ledger_path.with_suffix(".archive.jsonl")
        with archive_path.open("a", encoding="utf-8") as fh:
            for entry in archive:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        with ledger_path.open("w", encoding="utf-8") as fh:
            for entry in keep:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return len(archive)


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
    parser.add_argument(
        "--auto-resolve",
        action="store_true",
        help="auto-resolve incidents older than 24h with clear rules",
    )
    parser.add_argument(
        "--archive",
        action="store_true",
        help="archive resolved incidents older than 30 days",
    )
    parser.add_argument(
        "--archive-days",
        type=int,
        default=30,
        help="archive threshold in days (default: 30)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="with --auto-resolve or --archive, show count without modifying ledger",
    )
    args = parser.parse_args()

    if args.archive:
        count = archive_resolved(Path(args.ledger), days=args.archive_days, dry_run=args.dry_run)
        mode = "dry-run" if args.dry_run else "archived"
        print(f"archive: {count}건 {mode}")
        return 0

    if args.auto_resolve:
        count = auto_resolve(Path(args.ledger), dry_run=args.dry_run)
        mode = "dry-run" if args.dry_run else "resolved"
        print(f"auto-resolve: {count}건 {mode}")
        return 0

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
