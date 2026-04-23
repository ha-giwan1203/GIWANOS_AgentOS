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
  --op shadow_diff_readme  --path <README.md>
      (M2 합의: helper Python regex ↔ helper 내부 shell-equivalent 동등성 비교)

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
# M2 (세션96 2자 토론 Round 2 통과 합의):
# - GPT 보정 5-추가 B: shadow 기준을 helper↔shell parser 동등성으로 변경
# - 정규식 정교화: 블록쿼트(>) narrative 제외 + 마크다운 테이블 행만 매칭
# - final_check.sh:61-80의 awk+grep 의미와 동등 ("^## 활성 Hook" ~ "^## (훅별 실패|보조 스크립트)"
#   섹션의 "^| .*`name.sh` .*|" 테이블 행 카운트, 같은 구간의 `name.sh` 백틱 토큰 sort -u)


def extract_readme_hook_names(md_path: str) -> dict[str, Any]:
    """README 활성 Hook 섹션의 테이블 행에서 훅 이름 + 카운트 (Python regex 경로).

    셸 동등성: final_check.sh:61-80 readme_active_hook_count/_names의 awk+grep 의미 복제.
    - "## 활성 Hook" ~ "## (훅별 실패|보조 스크립트)" 사이 구간만 스캔
    - 마크다운 테이블 행(`^|` 시작 + `\\`name.sh\\`` 백틱 토큰 + 뒤에 `|` 포함)만 카운트
    - narrative blockquote(`>` 시작), 헤더, 본문 텍스트 제외

    반환: {"names": [...sort unique], "count": N (sort unique 수), "table_row_count": M (테이블 행 수)}
    """
    pth = Path(md_path)
    if not pth.exists():
        return {"names": [], "count": 0, "table_row_count": 0}
    content = pth.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()

    in_active_section = False
    table_row_count = 0
    names: list[str] = []
    # final_check.sh L67: '^| .*`[A-Za-z0-9_-]\+\.sh` .*|'
    table_row_pattern = re.compile(r"^\|.*`[A-Za-z0-9_-]+\.sh`.*\|")
    # final_check.sh L77: '`[A-Za-z0-9_-]+\.sh`'
    name_pattern = re.compile(r"`([A-Za-z0-9_-]+\.sh)`")

    for line in lines:
        if re.match(r"^## 활성 Hook", line):
            in_active_section = True
            continue
        if in_active_section and re.match(r"^## (훅별 실패|보조 스크립트)", line):
            break
        if not in_active_section:
            continue
        if not table_row_pattern.match(line):
            continue
        table_row_count += 1
        for m in name_pattern.finditer(line):
            names.append(m.group(1))

    unique = sorted(set(names))
    return {"names": unique, "count": len(unique), "table_row_count": table_row_count}


def _shell_equivalent_readme_hook_names(md_path: str) -> dict[str, Any]:
    """final_check.sh 셸 파서 의미를 헬퍼 내부에서 절차적으로 재구현 (shadow 비교용).

    GPT Round 2 권고: subprocess("bash -c awk+grep") 대신 헬퍼 내부 함수로
    재구현해 의존성·locale·속도 위험 회피. 의미는 final_check.sh L66-79와 동일.

    extract_readme_hook_names와 의도적으로 다른 구현 경로(절차적 line-by-line awk-style)
    를 사용해 두 경로가 같은 결과를 내는지 shadow_diff_readme에서 검증.
    """
    pth = Path(md_path)
    if not pth.exists():
        return {"names": [], "count": 0, "table_row_count": 0}

    flag = False  # awk의 flag 변수 — "## 활성 Hook" 진입 시 1, "## 훅별 실패|보조 스크립트" 진입 시 0
    table_rows: list[str] = []  # 테이블 행 라인 누적 (grep -c 대상)

    for raw_line in pth.read_text(encoding="utf-8", errors="replace").splitlines():
        # awk: /^## 활성 Hook/{flag=1; next}
        if raw_line.startswith("## 활성 Hook"):
            flag = True
            continue
        # awk: /^## (훅별 실패|보조 스크립트)/{flag=0}
        # awk 동작은 next 없으므로 다음 비교도 수행하지만, 이 라인은 grep 매치 안 됨
        if raw_line.startswith("## 훅별 실패") or raw_line.startswith("## 보조 스크립트"):
            flag = False
            continue
        # awk: flag (true이면 print)
        if not flag:
            continue
        # 셸: grep -c '^| .*`[A-Za-z0-9_-]\+\.sh` .*|'
        if not raw_line.startswith("|"):
            continue
        # 백틱으로 감싼 .sh 토큰 + 라인 끝에 | 포함 검사
        if "`" not in raw_line or "|" not in raw_line[1:]:
            continue
        # 라인 안에 `name.sh` 패턴이 최소 1개 + 그 뒤에 | 가 있어야
        match_iter = list(re.finditer(r"`([A-Za-z0-9_-]+\.sh)`", raw_line))
        if not match_iter:
            continue
        # 첫 매치 뒤에 |가 있는지 (셸 패턴 .*| 보장)
        first_end = match_iter[0].end()
        if "|" not in raw_line[first_end:]:
            continue
        table_rows.append(raw_line)

    # 셸: grep -oE | sed 's/`//g' | sort -u
    name_pattern = re.compile(r"`([A-Za-z0-9_-]+\.sh)`")
    name_set: set[str] = set()
    for line in table_rows:
        for m in name_pattern.finditer(line):
            name_set.add(m.group(1))

    return {
        "names": sorted(name_set),
        "count": len(name_set),
        "table_row_count": len(table_rows),
    }


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


# ── shadow_diff_readme: helper Python regex ↔ helper 내부 shell-equivalent 동등성 ──
def shadow_diff_readme(md_paths: list[str]) -> dict[str, Any]:
    """헬퍼 readme_hook_names(Python regex) ↔ _shell_equivalent_readme_hook_names 비교.

    M2 (세션96 2자 토론 Round 2 통과 합의 5-추가 B):
    - 본질: M2 목표가 helper의 셸 파서 의미 일치 검증이므로 README↔settings union이 아니라
      helper 자체의 두 구현 경로(Python regex vs 절차적 awk-style) 동등성을 본다.
    - GPT 권고: subprocess 대신 헬퍼 내부 함수로 재구현 (의존성·locale·속도)

    반환:
      {
        "match": bool,
        "py_count": N, "py_table_rows": M, "py_names": [...],
        "shell_equivalent_count": N, "shell_equivalent_table_rows": M, "shell_equivalent_names": [...],
        "only_in_py": [...], "only_in_shell_equivalent": [...]
      }
    """
    md_path = md_paths[0]
    py = extract_readme_hook_names(md_path)
    sh = _shell_equivalent_readme_hook_names(md_path)
    py_names = set(py["names"])
    sh_names = set(sh["names"])
    return {
        "match": (
            py_names == sh_names
            and py["count"] == sh["count"]
            and py.get("table_row_count") == sh.get("table_row_count")
        ),
        "py_count": py["count"],
        "py_table_rows": py.get("table_row_count"),
        "py_names": sorted(py_names),
        "shell_equivalent_count": sh["count"],
        "shell_equivalent_table_rows": sh.get("table_row_count"),
        "shell_equivalent_names": sorted(sh_names),
        "only_in_py": sorted(py_names - sh_names),
        "only_in_shell_equivalent": sorted(sh_names - py_names),
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
    "shadow_diff_readme": lambda args: shadow_diff_readme(args.path),
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
