#!/usr/bin/env python3
"""unresolved incident의 다음 수리 루프를 제안한다."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
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
        "send_block": "토론모드 CLAUDE.md 읽기 후 Skill(skill=\"debate-mode\") 또는 Skill(skill=\"gpt-send\")로 재전송 (세션93 자동수리: cdp_chat_send.py 폐기 반영)",
        "stop_guard_block": "독립 견해(반론/대안/내 판단)를 포함하여 재작성",
        "compile_fail": "문법 오류를 수정한 뒤 py_compile로 재검증",
        "harness_missing": "독립 분석(반론/대안)을 포함하여 하네스 분석 보완",
        "meta_drift": "TASKS/HANDOFF/STATUS 날짜를 동기화한 뒤 재확인",
        "test_fail": "실패한 테스트를 확인하고 원인 수정 후 재실행",
        "task_consecutive_fail": "스케줄 태스크 스크립트 점검 및 실행 환경 확인",
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
        "harness_missing": [
            ".claude/hooks/harness_gate.sh",
        ],
        "meta_drift": [
            "90_공통기준/업무관리/TASKS.md",
            "90_공통기준/업무관리/HANDOFF.md",
            "90_공통기준/업무관리/STATUS.md",
        ],
        "test_fail": [
            ".claude/hooks/smoke_test.sh",
            ".claude/hooks/e2e_test.sh",
        ],
        "task_consecutive_fail": [
            ".claude/logs/task_results.jsonl",
        ],
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
        "send_block": ["토론모드 CLAUDE.md 읽기", "Skill(skill=\"debate-mode\") 또는 Skill(skill=\"gpt-send\") 재호출"],
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
        return ["토론모드 CLAUDE.md 읽기", "Skill(skill=\"gpt-send\") 재호출 (세션93: CDP 폐기 반영)"]
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

    세션93 B-1 2자 토론 합의 (2026-04-22) — 확장 옵션 B (2+3+5):
    - send_block (navigate_gate): debate_claude_read.ok / debate_entry_read.ok
      mtime > incident ts 시 auto-resolve (상태 기반, 저위험)
    - python3_dependency (warn_recorded): final_check --fast WARN "python3 의존 잔존"
      현재 0건이면 일괄 auto-resolve (상태 기반, 저위험). A-2 반영으로 조건 충족
    - structural_intermediate (completion_gate): 24h 경과 시 시간 기반 auto-resolve
      (정보가치 소멸형, 과잉 정밀화 불필요)

    세션96 /auto-fix 규칙 6 — pre_commit_check 원인-해소 연결 (2자 토론 조건부 통과 반영):
    - 조건 (AND):
      1. classification_reason == "pre_commit_check"
      2. ts < now - 72h (최근 발생건 보존)
      3. detail 분기:
         - "final_check --fast FAIL": 현재 final_check --fast exit 0
         - "final_check --full FAIL": 현재 final_check --fast exit 0 + smoke_test.sh exit 0
    - 마킹: resolved_by="auto_rule6" + resolved_reason="pre_commit_check_stale_fast|full"
    - 로그: debate_20260423_112214

    세션96 incident 군집 정리 — 규칙 7~10 (2자 토론 Round 2 조건부 통과 반영):
    - rule 7 (harness_missing): 72h + 무재발 (key=(reason, hook, normalized_detail), latest_ts_by_key)
    - rule 8 (meta_drift): STATUS.md 현재 날짜 ≥ detail의 STATUS 날짜
    - rule 9 (doc_drift commit_gate WARN): 72h + detail 정확 일치 + 현재 final_check --fast stdout에 "문서 드리프트" 미포함
    - rule 10 (evidence_missing): 72h + 무재발 (key=fingerprint 우선 / fallback (hook, normalized_detail))
    - GPT Round 2 보정: latest_ts_by_key 단순화 + synthetic negative test
    - 로그: debate_20260423_130201/round3_gpt_incident.md, round4_gpt_incident.md

    세션96 활성 패턴 근본 원인 분석 — 규칙 11 (Wave 1, 2자 토론 Round 6 통과):
    - rule 11 (D0 stale allowlist 전용): 48h + (hook, normalized_detail) ∈ 3 tuples + 무재발
      - ("skill_instruction_gate", "MES access without SKILL.md read")
      - ("evidence_gate", "identifier_ref.req 존재. 기준정보 대조(identifier_ref.ok) 없이 관련 도메인 수정 금지.")
      - ("evidence_gate", "auth_diag.req 존재. auth_diag.ok 없이 MES/OAuth 관련 실행 금지.")
    - 의도: D0 인라인 개발(.claude/tmp/erp_d0_*.py) 부산물 21건 자연 소거 (정식 d0-production-plan/run.py 사용 후 무재발 시)
    - GPT Round 6 보정: detail-only 아닌 (hook, normalized_detail) 정확 쌍으로 좁혀 rule 10과 역할 분리
    - 마킹: resolved_by="auto_rule11", resolved_reason="d0_stale_<mes|identifier_ref|auth_diag>"
    - 로그: debate_20260423_130201/round5_claude_diagnosis.md, round6_gpt_incident.md

    방식: resolved=false → resolved=true + resolved_by 마킹으로 덮어쓰기
    """
    import datetime
    import os

    entries = load_jsonl(ledger_path)
    now = datetime.datetime.now(datetime.timezone.utc)
    count = 0

    # 세션93 B-1 제안 3: python3_dependency 일괄 해소 조건 사전 판정
    # final_check --fast가 현재 "python3 의존 잔존" WARN을 내지 않는다면 과거 기록 일괄 해소
    # 직접 호출은 순환 의존 가능성 → 간이 검사: .claude/hooks/*.sh에서 python3 직접 호출 grep
    py3_clean = True
    try:
        hooks_dir = ledger_path.parent / "hooks"
        if hooks_dir.exists():
            excluded = {"smoke_test.sh", "final_check.sh", "auto_compile.sh",
                        "skill_instruction_gate.sh"}
            for fn in hooks_dir.glob("*.sh"):
                if fn.name in excluded:
                    continue
                try:
                    content = fn.read_text(encoding="utf-8")
                    # "python3 -c" / "python3 -" 패턴 (PY_CMD 미적용 신호)
                    for line in content.splitlines():
                        stripped = line.lstrip()
                        if stripped.startswith("#"):
                            continue
                        if "python3 -c" in stripped or (" python3 -" in stripped and "PY_CMD" not in stripped):
                            py3_clean = False
                            break
                    if not py3_clean:
                        break
                except Exception:
                    pass
    except Exception:
        py3_clean = False  # 판정 실패 시 안전하게 해소 안 함

    # 세션93 B-1 제안 2: send_block .ok 마커 존재 여부 (상태 기반)
    project_root = ledger_path.parent.parent  # .claude/../ → 저장소 루트
    instr_dir = project_root / ".claude" / "state" / "instruction_reads"
    debate_claude_ok = instr_dir / "debate_claude_read.ok"
    debate_entry_ok = instr_dir / "debate_entry_read.ok"

    # 세션96 규칙 6: pre_commit_check 원인-해소 연결 (fast/full 분기)
    # 사전 1회 실행으로 현재 final_check --fast + smoke_test 통과 여부 캐시
    pre_commit_fast_pass = False
    pre_commit_full_pass = False
    try:
        fc_path = project_root / ".claude" / "hooks" / "final_check.sh"
        if fc_path.exists():
            r_fast = subprocess.run(
                ["bash", str(fc_path), "--fast"],
                cwd=str(project_root), capture_output=True, timeout=60
            )
            pre_commit_fast_pass = (r_fast.returncode == 0)
        st_path = project_root / ".claude" / "hooks" / "smoke_test.sh"
        if pre_commit_fast_pass and st_path.exists():
            r_full = subprocess.run(
                ["bash", str(st_path)],
                cwd=str(project_root), capture_output=True, timeout=180
            )
            pre_commit_full_pass = (r_full.returncode == 0)
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
        pass  # 실행 실패 시 해당 규칙 비활성 (안전측)

    def ok_mtime_after(ts_str: str) -> bool:
        """debate_claude_read.ok 또는 debate_entry_read.ok mtime이 incident ts 이후인지."""
        try:
            ts = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            incident_epoch = ts.timestamp()
            for ok_path in (debate_claude_ok, debate_entry_ok):
                if ok_path.exists():
                    if ok_path.stat().st_mtime > incident_epoch:
                        return True
        except Exception:
            pass
        return False

    # === 세션96 규칙 7~10 사전 캐시 (2자 토론 Round 2 통과 합의) ===
    def normalize_detail(s: str) -> str:
        """공백·개행 정규화. 백틱·따옴표는 보존 (의미 보존)."""
        return ' '.join((s or '').strip().split())

    # rule 7/10/11 무재발 검증용: latest_ts_by_key (GPT Round 2 보정 — list[ts] 대신 max(ts) 1개)
    # key 종류:
    #   - rule 7: (classification_reason, hook, normalized_detail) tuple
    #   - rule 10: fingerprint (있으면) / (hook, normalized_detail) tuple (없으면)
    #   - rule 11: (hook, normalized_detail) tuple, allowlist 3쌍에 한정
    latest_ts_by_key_rule7: dict = {}
    latest_ts_by_key_rule10_fp: dict = {}     # fingerprint 키
    latest_ts_by_key_rule10_hd: dict = {}     # (hook, norm_detail) 키
    latest_ts_by_key_rule11: dict = {}        # (hook, norm_detail) 키, allowlist만
    # rule 11 — D0 stale 패턴 allowlist (GPT Round 6 보정: detail-only 아닌 정확 쌍 3개)
    rule11_allowlist = {
        ("skill_instruction_gate", "MES access without SKILL.md read"): "mes",
        ("evidence_gate", "identifier_ref.req 존재. 기준정보 대조(identifier_ref.ok) 없이 관련 도메인 수정 금지."): "identifier_ref",
        ("evidence_gate", "auth_diag.req 존재. auth_diag.ok 없이 MES/OAuth 관련 실행 금지."): "auth_diag",
    }
    for e in entries:
        ts_e = e.get("ts", "")
        if not ts_e:
            continue
        reason_e = e.get("classification_reason") or ""
        hook_e = e.get("hook") or ""
        nd_e = normalize_detail(e.get("detail") or "")
        # rule 7 키
        if reason_e == "harness_missing":
            key7 = (reason_e, hook_e, nd_e)
            prev = latest_ts_by_key_rule7.get(key7, "")
            if ts_e > prev:
                latest_ts_by_key_rule7[key7] = ts_e
        # rule 10 키
        if reason_e == "evidence_missing":
            fp = e.get("fingerprint")
            if fp:
                prev = latest_ts_by_key_rule10_fp.get(fp, "")
                if ts_e > prev:
                    latest_ts_by_key_rule10_fp[fp] = ts_e
            else:
                key10 = (hook_e, nd_e)
                prev = latest_ts_by_key_rule10_hd.get(key10, "")
                if ts_e > prev:
                    latest_ts_by_key_rule10_hd[key10] = ts_e
        # rule 11 키 (allowlist 한정)
        if reason_e == "evidence_missing":
            key11 = (hook_e, nd_e)
            if key11 in rule11_allowlist:
                prev = latest_ts_by_key_rule11.get(key11, "")
                if ts_e > prev:
                    latest_ts_by_key_rule11[key11] = ts_e

    # rule 8: STATUS.md 현재 날짜 캐시
    current_status_date = ""
    try:
        status_path = project_root / "90_공통기준" / "업무관리" / "STATUS.md"
        if status_path.exists():
            content = status_path.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"최종 업데이트:\s*(\d{4}-\d{2}-\d{2})", content)
            if m:
                current_status_date = m.group(1)
    except Exception:
        pass

    # rule 9: 현재 final_check --fast stdout에 "문서 드리프트" 미포함 캐시
    # Windows Python subprocess의 시스템 기본 디코딩(cp949)이 한글 stdout 처리 실패하므로 utf-8 강제
    doc_drift_currently_clean = False
    try:
        fc_path = project_root / ".claude" / "hooks" / "final_check.sh"
        if fc_path.exists():
            r = subprocess.run(
                ["bash", str(fc_path), "--fast"],
                cwd=str(project_root), capture_output=True, timeout=60,
                encoding="utf-8", errors="replace"
            )
            combined = (r.stdout or "") + (r.stderr or "")
            doc_drift_currently_clean = ("문서 드리프트" not in combined)
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
        pass  # 실패 시 비활성 (안전측)

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
        # 세션96 rule 11 도입: allowlist (hook, normalized_detail) 쌍은 rule 11이 처리하므로
        #   기존 24h fallback 비활성 (rule 11 48h + 무재발 안전장치 적용)
        if reason == "evidence_missing" or hook in ("evidence_gate", "evidence_stop_guard"):
            detail = entry.get("detail") or ""
            # detail에서 .req 파일 경로 추출 → 대응 .ok 파일 존재 여부 확인
            req_file = entry.get("file") or ""
            if req_file and req_file.endswith(".req"):
                ok_file = req_file[:-4] + ".ok"
                if Path(ok_file).exists():
                    should_resolve = True
            elif req_file == "" and detail:
                # rule 11 allowlist 케이스는 rule 11에 위임 (기존 24h fallback 우회)
                if (hook, normalize_detail(detail)) in rule11_allowlist:
                    pass
                else:
                    # file 필드 없으면 시간 기반 fallback (하위 호환)
                    ts_str = entry.get("ts", "")
                    try:
                        ts = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        if (now - ts).total_seconds() > 86400:
                            should_resolve = True
                    except (ValueError, TypeError):
                        pass

        # 세션96 규칙 6: pre_commit_check 원인-해소 연결 (2자 토론 조건부 통과 반영)
        # detail 분기 — fast FAIL: final_check --fast PASS로 해소 / full FAIL: + smoke_test PASS 추가
        if reason == "pre_commit_check":
            ts_str = entry.get("ts", "")
            detail = entry.get("detail") or ""
            try:
                ts = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if (now - ts).total_seconds() > 72 * 3600:  # 72h 버퍼
                    if "final_check --fast FAIL" in detail and pre_commit_fast_pass:
                        should_resolve = True
                        entry["_rule6_variant"] = "fast"
                    elif "final_check --full FAIL" in detail and pre_commit_fast_pass and pre_commit_full_pass:
                        should_resolve = True
                        entry["_rule6_variant"] = "full"
            except (ValueError, TypeError):
                pass

        # 세션93 B-1 제안 2: send_block (navigate_gate) — .ok 마커 mtime 기반
        if reason == "send_block" or hook == "navigate_gate":
            ts_str = entry.get("ts", "")
            if ok_mtime_after(ts_str):
                should_resolve = True

        # 세션93 B-1 제안 3: python3_dependency (warn_recorded) — 현재 WARN 0 일괄 해소
        if reason == "python3_dependency":
            if py3_clean:
                should_resolve = True

        # 세션93 B-1 제안 5: structural_intermediate (completion_gate) — 24h 시간 기반
        if reason == "structural_intermediate":
            ts_str = entry.get("ts", "")
            try:
                ts = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if (now - ts).total_seconds() > 86400:
                    should_resolve = True
            except (ValueError, TypeError):
                pass

        # === 세션96 규칙 7~10 (2자 토론 Round 2 통과 합의) ===
        ts_str = entry.get("ts", "")
        nd = normalize_detail(entry.get("detail") or "")

        # rule 7 — harness_missing: 72h + 무재발 (key=(reason, hook, normalized_detail))
        if reason == "harness_missing":
            try:
                ts = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if (now - ts).total_seconds() > 72 * 3600:
                    key7 = (reason, hook, nd)
                    latest = latest_ts_by_key_rule7.get(key7, "")
                    # 이 incident가 같은 키의 최신 ts인 경우만 해소 (이후 재발 0)
                    if ts_str >= latest:
                        should_resolve = True
                        entry["_rule7_marker"] = True
            except (ValueError, TypeError):
                pass

        # rule 8 — meta_drift: STATUS.md 현재 날짜가 detail의 STATUS 날짜 이상
        if reason == "meta_drift" and current_status_date:
            detail = entry.get("detail") or ""
            m = re.search(r"STATUS\((\d{4}-\d{2}-\d{2})\)\s*<\s*TASKS", detail)
            if m:
                detail_status_date = m.group(1)
                if current_status_date >= detail_status_date:
                    should_resolve = True
                    entry["_rule8_marker"] = True

        # rule 9 — doc_drift commit_gate WARN: 72h + 정확 일치 + 현재 final_check clean
        if (reason == "doc_drift" and hook == "commit_gate"
                and entry.get("type") == "warn_recorded"
                and (entry.get("detail") or "").strip() == "문서 드리프트 감지"
                and doc_drift_currently_clean):
            try:
                ts = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if (now - ts).total_seconds() > 72 * 3600:
                    should_resolve = True
                    entry["_rule9_marker"] = True
            except (ValueError, TypeError):
                pass

        # rule 10 — evidence_missing: 72h 항상 필수 + 무재발
        # key: fingerprint 우선 / 없으면 (hook, normalized_detail)
        if reason == "evidence_missing":
            try:
                ts = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if (now - ts).total_seconds() > 72 * 3600:
                    fp = entry.get("fingerprint")
                    if fp:
                        latest = latest_ts_by_key_rule10_fp.get(fp, "")
                    else:
                        latest = latest_ts_by_key_rule10_hd.get((hook, nd), "")
                    if ts_str >= latest:
                        should_resolve = True
                        entry["_rule10_marker"] = True
            except (ValueError, TypeError):
                pass

        # rule 11 — D0 stale allowlist 전용 (GPT Round 6: (hook, normalized_detail) 정확 쌍)
        # 의도: D0 인라인 개발 부산물 자연 소거. 즉시 효과 0건이 정상.
        if reason == "evidence_missing":
            key11 = (hook, nd)
            if key11 in rule11_allowlist:
                try:
                    ts = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if (now - ts).total_seconds() > 48 * 3600:
                        latest = latest_ts_by_key_rule11.get(key11, "")
                        if ts_str >= latest:
                            should_resolve = True
                            entry["_rule11_marker"] = rule11_allowlist[key11]
                except (ValueError, TypeError):
                    pass

        if should_resolve:
            entry["resolved"] = True
            variant = entry.pop("_rule6_variant", None)
            r7 = entry.pop("_rule7_marker", False)
            r8 = entry.pop("_rule8_marker", False)
            r9 = entry.pop("_rule9_marker", False)
            r10 = entry.pop("_rule10_marker", False)
            r11 = entry.pop("_rule11_marker", None)  # str sub-id or None
            if reason == "pre_commit_check" and variant:
                entry["resolved_by"] = "auto_rule6"
                entry["resolved_reason"] = f"pre_commit_check_stale_{variant}"
            elif r7:
                entry["resolved_by"] = "auto_rule7"
                entry["resolved_reason"] = "harness_block_no_recurrence"
            elif r8:
                entry["resolved_by"] = "auto_rule8"
                entry["resolved_reason"] = "meta_drift_status_caught_up"
            elif r9:
                entry["resolved_by"] = "auto_rule9"
                entry["resolved_reason"] = "doc_drift_currently_clean"
            elif r10:
                entry["resolved_by"] = "auto_rule10"
                entry["resolved_reason"] = "evidence_block_no_recurrence"
            elif r11:
                entry["resolved_by"] = "auto_rule11"
                entry["resolved_reason"] = f"d0_stale_{r11}"
            else:
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


def backfill_classification(ledger_path: Path, dry_run: bool = False) -> int:
    """빈 classification_reason을 hook 필드 기반으로 소급 태깅.

    세션40 GPT 토론 합의: resolved로 덮지 말고 분류만 채운다.
    ts/detail/file/resolved 보존, classification_reason만 추가.
    """
    HOOK_TO_REASON: dict[str, str] = {
        "commit_gate": "pre_commit_check",
        "evidence_gate": "evidence_missing",
        "evidence_stop_guard": "evidence_missing",
        "date_scope_guard": "scope_violation",
        "block_dangerous": "dangerous_cmd",
        "stop_guard": "stop_guard_block",
        "send_gate": "send_block",
        "harness_gate": "harness_missing",
    }
    entries = load_jsonl(ledger_path)
    count = 0
    for entry in entries:
        reason = (entry.get("classification_reason") or "").strip()
        if reason:
            continue
        hook = entry.get("hook", "")
        detail = entry.get("detail", "")
        # hook 기반 매핑
        if hook in HOOK_TO_REASON:
            entry["classification_reason"] = HOOK_TO_REASON[hook]
            count += 1
        elif hook == "completion_gate":
            fp = entry.get("false_positive")
            if fp:
                entry["classification_reason"] = "structural_intermediate"
            elif "Git" in detail or "commit" in detail or "push" in detail:
                entry["classification_reason"] = "completion_before_git"
            elif "TASKS" in detail or "HANDOFF" in detail:
                entry["classification_reason"] = "completion_before_state_sync"
            else:
                entry["classification_reason"] = "legacy_unclassified"
            count += 1
        elif hook == "instruction_not_read":
            entry["classification_reason"] = "evidence_missing"
            count += 1
        else:
            entry["classification_reason"] = "legacy_unclassified"
            count += 1
    if not dry_run and count > 0:
        fd, tmp_path = tempfile.mkstemp(dir=str(ledger_path.parent), suffix=".tmp")
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
    parser.add_argument(
        "--backfill-classification",
        action="store_true",
        help="빈 classification_reason을 hook 기반으로 소급 태깅",
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

    if args.backfill_classification:
        count = backfill_classification(Path(args.ledger), dry_run=args.dry_run)
        mode = "dry-run" if args.dry_run else "backfilled"
        print(f"backfill: {count}건 {mode}")
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
