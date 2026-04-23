#!/usr/bin/env python3
"""파싱 공통층 헬퍼 — list_active_hooks / final_check / risk_profile_prompt의
손파싱(정규식/awk/grep)을 단일 Python 모듈로 통합.

세션96 /auto-fix 2자 토론 (debate_20260423_122413) — GPT 조건부 통과 수정안 반영:
- domain_registry: YAML → JSON (.claude/domain_entry_registry.json)
- count만 → count + 이름 리스트 병행 제공
- JSON 단일 출력 계약 (셸 재파싱 금지)
- 1단계 범위: list_active_hooks + final_check 파싱만. risk_profile_prompt는 M4

CLI 호출 패턴:
    python parse_helpers.py --op <op> [--path <p>]...

  --op hooks_from_settings --path <settings.json> [--path <settings.local.json>]
  --op readme_hook_names   --path <README.md>
  --op status_hook_count   --path <STATUS.md>
  --op domain_entries      --path <domain_entry_registry.json>
  --op doc_dates           --path <TASKS.md>
  --op doc_session         --path <TASKS.md>
  --op shadow_diff_active_hooks --path <settings.json> --path <settings.local.json>
      (list_active_hooks.sh 결과와 헬퍼 결과 diff, shadow mode 검증용)

모든 출력은 JSON 단일 포맷. 에러는 {"error": "..."} + exit 2.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


# ── settings.json 훅 파싱 ─────────────────────────────────────
def parse_hooks_from_settings(json_paths: list[str]) -> dict[str, Any]:
    """settings.json (team+local) union 훅 리스트.

    반환:
      {
        "by_event": {"PreToolUse": ["block_dangerous.sh", ...], ...},
        "all_names": ["block_dangerous.sh", ...],  # 고유 정렬
        "total": 31,
        "counts_by_event": {"PreToolUse": 16, ...}
      }
    """
    events: dict[str, set[str]] = defaultdict(set)
    for p in json_paths:
        pth = Path(p)
        if not pth.exists():
            continue
        try:
            data = json.loads(pth.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for evt, handlers in (data.get("hooks") or {}).items():
            for h in handlers or []:
                for hh in (h.get("hooks") or []):
                    if hh.get("type") != "command":
                        continue
                    cmd = hh.get("command", "")
                    # bash .claude/hooks/NAME.sh 패턴만 추출
                    if "bash " in cmd and ".claude/hooks/" in cmd:
                        name = cmd.split(".claude/hooks/")[-1].split()[0].strip()
                        if name.endswith(".sh"):
                            events[evt].add(name)

    all_names: set[str] = set()
    for names in events.values():
        all_names.update(names)

    by_event = {evt: sorted(names) for evt, names in events.items()}
    counts_by_event = {evt: len(names) for evt, names in by_event.items()}

    return {
        "by_event": by_event,
        "all_names": sorted(all_names),
        "total": len(all_names),
        "counts_by_event": counts_by_event,
    }


# ── README 훅 이름 추출 ───────────────────────────────────────
def extract_readme_hook_names(md_path: str) -> dict[str, Any]:
    """README 활성 Hook 섹션에서 훅 이름 + 카운트.

    기존 final_check.sh:61-77 readme_active_hook_count/readme_active_hook_names
    awk 로직을 Python으로 포팅.

    반환: {"names": [...], "count": N}
    """
    pth = Path(md_path)
    if not pth.exists():
        return {"names": [], "count": 0}
    content = pth.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()

    in_active_section = False
    names: list[str] = []
    for line in lines:
        if re.match(r"^## 활성 Hook", line):
            in_active_section = True
            continue
        if in_active_section and re.match(r"^## (훅별 실패|보조 스크립트)", line):
            break
        if not in_active_section:
            continue
        # 훅 이름 패턴: .sh로 끝나는 코드 토큰 (백틱 또는 공백 경계)
        for m in re.finditer(r"[`\s]([a-z_][a-z0-9_]*\.sh)", line):
            names.append(m.group(1))

    unique = sorted(set(names))
    return {"names": unique, "count": len(unique)}


# ── STATUS.md 훅 수 추출 ──────────────────────────────────────
def extract_status_hook_count(md_path: str) -> dict[str, Any]:
    """STATUS.md hooks 체계 행에서 "N개 등록" 숫자 추출.

    반환: {"count": N | None}
    """
    pth = Path(md_path)
    if not pth.exists():
        return {"count": None}
    content = pth.read_text(encoding="utf-8", errors="replace")
    # 패턴: "31개 등록" / "31 개 등록"
    m = re.search(r"(\d+)\s*개\s*등록", content)
    return {"count": int(m.group(1)) if m else None}


# ── domain_entry_registry.json 로드 ──────────────────────────
def load_domain_entries(json_path: str) -> dict[str, Any]:
    """domain_entry_registry.json 로드 (YAML 아님 — GPT 지적 반영)."""
    pth = Path(json_path)
    if not pth.exists():
        return {"error": f"not_found: {json_path}"}
    try:
        return json.loads(pth.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return {"error": f"json_decode: {e}"}


# ── TASKS/HANDOFF/STATUS 최종 업데이트 날짜/세션 추출 ───────────
def extract_doc_dates(md_path: str) -> dict[str, Any]:
    """'최종 업데이트: YYYY-MM-DD' 추출."""
    pth = Path(md_path)
    if not pth.exists():
        return {"date": None}
    content = pth.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"최종 업데이트:\s*(\d{4}-\d{2}-\d{2})", content)
    return {"date": m.group(1) if m else None}


def extract_doc_session(md_path: str) -> dict[str, Any]:
    """'세션N' 첫 매치 숫자 추출."""
    pth = Path(md_path)
    if not pth.exists():
        return {"session": None}
    content = pth.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"세션(\d+)", content)
    return {"session": int(m.group(1)) if m else None}


# ── Shadow mode 검증 ────────────────────────────────────────
def shadow_diff_active_hooks(json_paths: list[str]) -> dict[str, Any]:
    """list_active_hooks.sh(inline) 결과와 parse_hooks_from_settings 결과 비교.

    shadow mode 1주 관찰 규칙 (GPT 조건부 통과 조건):
    두 파싱 경로 결과가 일치하는지 검증. 다르면 diff 반환.

    반환: {"match": bool, "diff": {...}, "helper": {...}, "inline": {...}}
    """
    # 헬퍼 결과
    helper = parse_hooks_from_settings(json_paths)

    # inline 재구현 — list_active_hooks.sh의 Python heredoc과 동일 로직
    # (의도적으로 중복: shadow 비교를 위한 독립 구현)
    events_inline: dict[str, set[str]] = defaultdict(set)
    for p in json_paths:
        pth = Path(p)
        if not pth.exists():
            continue
        try:
            data = json.loads(pth.read_text(encoding="utf-8"))
        except Exception:
            continue
        for evt, handlers in (data.get("hooks") or {}).items():
            for h in handlers or []:
                for hh in (h.get("hooks") or []):
                    if hh.get("type") != "command":
                        continue
                    cmd = hh.get("command", "")
                    if "bash " in cmd and ".claude/hooks/" in cmd:
                        name = cmd.split(".claude/hooks/")[-1].split()[0].strip()
                        if name.endswith(".sh"):
                            events_inline[evt].add(name)

    inline_all = set()
    for names in events_inline.values():
        inline_all.update(names)

    helper_all = set(helper["all_names"])
    match = inline_all == helper_all
    diff_only_helper = sorted(helper_all - inline_all)
    diff_only_inline = sorted(inline_all - helper_all)

    return {
        "match": match,
        "helper_total": len(helper_all),
        "inline_total": len(inline_all),
        "only_in_helper": diff_only_helper,
        "only_in_inline": diff_only_inline,
    }


# ── CLI ─────────────────────────────────────────────────────
OPS = {
    "hooks_from_settings": lambda args: parse_hooks_from_settings(args.path),
    "readme_hook_names": lambda args: extract_readme_hook_names(args.path[0]),
    "status_hook_count": lambda args: extract_status_hook_count(args.path[0]),
    "domain_entries": lambda args: load_domain_entries(args.path[0]),
    "doc_dates": lambda args: extract_doc_dates(args.path[0]),
    "doc_session": lambda args: extract_doc_session(args.path[0]),
    "shadow_diff_active_hooks": lambda args: shadow_diff_active_hooks(args.path),
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--op", required=True, choices=list(OPS.keys()))
    ap.add_argument("--path", action="append", default=[], help="파일 경로 (복수 가능)")
    args = ap.parse_args()

    if args.op not in OPS:
        print(json.dumps({"error": f"unknown op: {args.op}"}, ensure_ascii=False))
        return 2

    if not args.path and args.op in ("readme_hook_names", "status_hook_count",
                                      "domain_entries", "doc_dates", "doc_session"):
        print(json.dumps({"error": f"--path required for op: {args.op}"}, ensure_ascii=False))
        return 2

    try:
        result = OPS[args.op](args)
    except Exception as e:  # 헬퍼 실패는 런타임 에러로 격리
        print(json.dumps({"error": f"{type(e).__name__}: {e}"}, ensure_ascii=False))
        return 2

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
