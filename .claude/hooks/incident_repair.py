#!/usr/bin/env python3
"""unresolved incident의 다음 수리 루프를 제안한다."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
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

    reason = entry.get("classification_reason") or ""
    hook = entry.get("hook") or ""
    detail = entry.get("detail") or ""

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
    hook = entry.get("hook") or ""
    classification = entry.get("classification_reason") or ""
    file_field = (entry.get("file") or "").strip()
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
    reason = entry.get("classification_reason") or ""
    hook = entry.get("hook") or ""
    detail = entry.get("detail") or ""

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

    자동 해소 대상 (세션15 GPT+Claude 합의 — 유형별 분기):
    - scope_violation: 24시간 경과 시 (1회성 차단)
    - dangerous_cmd: 24시간 경과 시 (1회성 차단)
    - evidence_missing: 대응 .ok 파일 존재 시에만 (시간 무관)
    - pre_commit_check: auto-resolve 대상 제외 (PASS 마커 체계 미비)

    방식: resolved=false → resolved=true + resolved_by="auto" 로 덮어쓰기
    """
    import datetime

    entries = load_jsonl(ledger_path)
    now = datetime.datetime.now(datetime.timezone.utc)
    count = 0

    for entry in entries:
        if entry.get("resolved"):
            continue
        reason = entry.get("classification_reason") or ""
        hook = entry.get("hook") or ""

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

        # evidence_missing: .ok 증거 파일 존재 시에만 auto-resolve (세션15 합의)
        if reason == "evidence_missing" or hook in ("evidence_gate", "evidence_stop_guard"):
            detail = entry.get("detail") or ""
            # detail에서 .req 파일 경로 추출 → 대응 .ok 파일 존재 여부 확인
            req_file = entry.get("file") or ""
            if req_file and req_file.endswith(".req"):
                ok_file = req_file[:-4] + ".ok"
                if Path(ok_file).exists():
                    should_resolve = True
            elif req_file == "" and detail:
                # file 필드 없으면 시간 기반 fallback (하위 호환)
                ts_str = entry.get("ts", "")
                try:
                    ts = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if (now - ts).total_seconds() > 86400:
                        should_resolve = True
                except (ValueError, TypeError):
                    pass

        # pre_commit_check: auto-resolve 대상 제외 (세션15 합의)
        # PASS 마커 체계 미비 → 수동 해소만 허용
        # (이전: 24시간 경과 시 자동 해소)

        if should_resolve:
            entry["resolved"] = True
            entry["resolved_by"] = "auto"
            count += 1

    if not dry_run and count > 0:
        # 원자적 쓰기 (세션14)
        fd, tmp_path = tempfile.mkstemp(
            dir=str(ledger_path.parent), suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                for entry in entries:
                    fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
            os.replace(tmp_path, str(ledger_path))
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    return count


def parse_test_output(output: str) -> list[dict[str, Any]]:
    """smoke_test.sh / e2e_test.sh 출력에서 [FAIL] 라인을 파싱해 incident 포맷으로 변환.

    Phase 3-1: 오토리서치 루프 기반.
    반환 형식: [{"hook": "smoke_test|e2e_test", "type": "test_fail",
                 "detail": "FAIL 내용", "classification_reason": "test_fail",
                 "inferred_next_action": "...", "patch_candidates": [...]}]
    """
    import re
    import datetime

    incidents: list[dict[str, Any]] = []
    current_section = ""
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

    for line in output.splitlines():
        # 섹션 헤더 감지: "--- 1. hook_common.sh ---" 또는 "--- E2E-1. ..."
        section_match = re.match(r"---\s*(.*?)\s*---", line)
        if section_match:
            current_section = section_match.group(1).strip()
            continue

        # [FAIL] 라인 감지
        if "[FAIL]" in line:
            detail = line.strip().replace("[FAIL] ", "").strip()
            # 테스트 유형 판별
            is_e2e = "E2E" in current_section or "e2e" in current_section.lower()
            hook_name = "e2e_test" if is_e2e else "smoke_test"

            # 패치 후보 추론: detail에서 파일명/함수명 추출
            candidates: list[str] = []
            file_match = re.search(r"(\S+\.(sh|py|json|md))", detail)
            if file_match:
                candidates.append(f".claude/hooks/{file_match.group(1)}")

            # 다음 행동 추론
            if "존재" in detail or "없" in detail:
                next_action = f"파일 존재/내용 확인: {detail}"
            elif "등록" in detail:
                next_action = f"settings.local.json 등록 확인: {detail}"
            elif "함수" in detail or "정의" in detail:
                next_action = f"함수 정의/참조 확인: {detail}"
            else:
                next_action = f"FAIL 항목 직접 확인 후 수정: {detail}"

            incidents.append({
                "ts": ts,
                "hook": hook_name,
                "type": "test_fail",
                "detail": detail,
                "section": current_section,
                "classification_reason": "test_fail",
                "inferred_next_action": next_action,
                "patch_candidates": candidates,
                "verify_steps": [
                    f"bash .claude/hooks/{'e2e_test' if is_e2e else 'smoke_test'}.sh"
                ],
            })

    return incidents


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
        # 원자적 쓰기: temp 파일 → os.replace (세션14: 중단 시 데이터 손실 방지)
        fd, tmp_path = tempfile.mkstemp(
            dir=str(ledger_path.parent), suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                for entry in keep:
                    fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
            os.replace(tmp_path, str(ledger_path))
        except Exception:
            # 실패 시 temp 파일 정리 — 원본 ledger는 보존됨
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

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
    parser.add_argument(
        "--parse-test-output",
        type=str,
        default=None,
        metavar="FILE",
        help="smoke/e2e test output file to parse for FAIL incidents",
    )
    args = parser.parse_args()

    # Phase 3-1: smoke/e2e FAIL 파싱
    if args.parse_test_output:
        test_path = Path(args.parse_test_output)
        if not test_path.exists():
            print(f"파일 없음: {args.parse_test_output}")
            return 1
        output = test_path.read_text(encoding="utf-8")
        incidents = parse_test_output(output)
        if not incidents:
            print("FAIL 없음 — ALL PASS.")
            return 0
        if args.json:
            print(json.dumps(incidents, ensure_ascii=False, indent=2))
        else:
            print(f"FAIL {len(incidents)}건 발견:")
            for inc in incidents:
                print(f"  [{inc['hook']}] {inc['detail']}")
                print(f"    → 다음 행동: {inc['inferred_next_action']}")
                if inc.get("patch_candidates"):
                    print(f"    → 패치 후보: {', '.join(inc['patch_candidates'])}")
        return 0

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
