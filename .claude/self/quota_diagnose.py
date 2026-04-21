#!/usr/bin/env python3
"""Self-X Layer 2/4 — Subtraction Quota 진단 + 4등급 분류 산출.

debate_20260421_142204_3way (B5 3way 만장일치 통과) 구현.

기능:
- raw 카운트 + 활성 등록 카운트 분리 측정
- 4단계 안전 검증 (보호리스트/30일 호출 0/타 모듈 참조 없음/대체 경로)
- 4등급 분류: 삭제금지 / 병합후삭제 / 아카이브우선 / 즉시삭제후보
- 고아(Orphan) 0순위: 30일 호출 0 + 참조 없음 + 보호리스트 제외

Usage:
  python3 .claude/self/quota_diagnose.py            # 정원 상태 + 후보 표시
  python3 .claude/self/quota_diagnose.py --json     # JSON 출력
  python3 .claude/self/quota_diagnose.py --orphans  # 고아만
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROTECTED_FILE = PROJECT_ROOT / "90_공통기준" / "protected_assets.yaml"
HOOK_LOG = PROJECT_ROOT / ".claude" / "hooks" / "hook_log.jsonl"
SETTINGS = PROJECT_ROOT / ".claude" / "settings.json"


def load_protected() -> dict:
    """protected_assets.yaml 파싱 (간단 파서)."""
    if not PROTECTED_FILE.exists():
        return {"protected_paths": set(), "quota": {}, "ttl": {}}
    text = PROTECTED_FILE.read_text(encoding="utf-8")
    paths = set()
    quota = {}
    ttl = {}
    in_protected = False
    in_quota = False
    in_ttl = False
    current_section_subkey = None
    current_quota_block = None
    current_ttl_block = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "protected:":
            in_protected, in_quota, in_ttl = True, False, False
            continue
        if stripped == "quota:":
            in_protected, in_quota, in_ttl = False, True, False
            continue
        if stripped == "ttl:":
            in_protected, in_quota, in_ttl = False, False, True
            continue
        if in_protected and stripped.startswith("- path:"):
            p = stripped.split("path:", 1)[1].strip()
            paths.add(p)
        if in_quota:
            m = re.match(r"^(\w+):$", stripped)
            if m and not stripped.startswith("- "):
                current_quota_block = m.group(1)
                quota[current_quota_block] = {}
                continue
            m2 = re.match(r"^(\w+):\s*(\S.*)?$", stripped)
            if m2 and current_quota_block:
                k = m2.group(1).strip()
                v = (m2.group(2) or "").strip()
                # 인라인 주석 제거
                v = v.split("#", 1)[0].strip()
                if k not in ["raw_initial", "activate_target", "glide_path"]:
                    continue
                quota[current_quota_block][k] = int(v) if v.isdigit() else v
        if in_ttl:
            m = re.match(r"^(\w+):$", stripped)
            if m:
                current_ttl_block = m.group(1)
                ttl[current_ttl_block] = {}
                continue
            m2 = re.match(r"^(\w+):\s*(\d+)$", stripped)
            if m2 and current_ttl_block:
                ttl[current_ttl_block][m2.group(1)] = int(m2.group(2))
    return {"protected_paths": paths, "quota": quota, "ttl": ttl}


def count_files(category: str) -> tuple[int, list[Path]]:
    """raw 파일 카운트 + 경로 리스트."""
    if category == "hook":
        files = sorted((PROJECT_ROOT / ".claude" / "hooks").glob("*.sh"))
    elif category == "command":
        files = sorted((PROJECT_ROOT / ".claude" / "commands").glob("*.md"))
    elif category == "agent":
        files = sorted((PROJECT_ROOT / ".claude" / "agents").glob("*.md"))
    else:
        files = []
    return len(files), files


def count_active_hooks() -> int:
    """settings.json에 등록된 활성 hook 수."""
    try:
        s = json.loads(SETTINGS.read_text(encoding="utf-8"))
    except Exception:
        return 0
    hooks = s.get("hooks", {})
    count = 0
    seen = set()
    for category, items in hooks.items():
        for item in items if isinstance(items, list) else [items]:
            for h in item.get("hooks", []) if isinstance(item, dict) else []:
                cmd = h.get("command", "")
                m = re.search(r"\.claude/hooks/(\S+\.sh)", cmd)
                if m:
                    name = m.group(1)
                    if name not in seen:
                        seen.add(name)
                        count += 1
    return count


def hook_log_calls_30d() -> dict[str, int]:
    """hook_log.jsonl에서 최근 30일 hook별 호출 횟수."""
    counts: dict[str, int] = {}
    if not HOOK_LOG.exists():
        return counts
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    try:
        for line in HOOK_LOG.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                ts = r.get("ts", "")
                hook = r.get("hook", "")
                if hook and ts:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    if dt > cutoff:
                        counts[hook] = counts.get(hook, 0) + 1
            except Exception:
                continue
    except Exception:
        pass
    return counts


def find_references(hook_name: str) -> int:
    """저장소 내 hook_name 참조 수 (settings 외)."""
    pattern = hook_name.replace(".sh", "")
    refs = 0
    try:
        for p in PROJECT_ROOT.rglob("*.sh"):
            if p.name == hook_name:
                continue
            if pattern in p.read_text(encoding="utf-8", errors="ignore"):
                refs += 1
        for p in PROJECT_ROOT.rglob("*.md"):
            if pattern in p.read_text(encoding="utf-8", errors="ignore"):
                refs += 1
    except Exception:
        pass
    return refs


def classify(file_path: Path, protected: set, calls: dict) -> str:
    """4등급 분류: 삭제금지 / 병합후삭제 / 아카이브우선 / 즉시삭제후보."""
    rel = str(file_path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    if rel in protected:
        return "삭제금지"

    name = file_path.name
    age_days = (time.time() - file_path.stat().st_mtime) / 86400
    call_count = calls.get(name.replace(".sh", ""), 0)
    refs = find_references(name)

    if call_count == 0 and refs == 0 and age_days > 30:
        return "즉시삭제후보"  # 고아
    if age_days > 90 and call_count < 5:
        return "아카이브우선"
    if call_count < 3 and refs <= 1:
        return "병합후삭제"
    return "유지"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--orphans", action="store_true")
    parser.add_argument("--quick", action="store_true", help="references 검색 생략 (빠름, advisory용)")
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    cfg = load_protected()
    protected_paths = cfg["protected_paths"]
    quota = cfg["quota"]

    raw_hook, hook_files = count_files("hook")
    raw_cmd, cmd_files = count_files("command")
    raw_agent, agent_files = count_files("agent")
    active_hook = count_active_hooks()
    calls = hook_log_calls_30d()

    candidates = []
    if not args.quick:
        for f in hook_files:
            cls = classify(f, protected_paths, calls)
            if cls != "유지":
                rel = str(f.relative_to(PROJECT_ROOT)).replace("\\", "/")
                candidates.append({"path": rel, "class": cls,
                                  "calls_30d": calls.get(f.name.replace(".sh", ""), 0),
                                  "refs": find_references(f.name),
                                  "age_days": int((time.time() - f.stat().st_mtime) / 86400)})

    payload = {
        "ts": datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M KST"),
        "quota": {
            "hook": {"raw": raw_hook, "active": active_hook,
                     "raw_initial": quota.get("hook", {}).get("raw_initial", 0),
                     "active_target": quota.get("hook", {}).get("activate_target", 0)},
            "command": {"raw": raw_cmd, "target": quota.get("command", {}).get("activate_target", 0)},
            "agent": {"raw": raw_agent, "target": quota.get("agent", {}).get("activate_target", 0)},
        },
        "candidates": sorted(candidates, key=lambda x: (
            {"즉시삭제후보": 0, "아카이브우선": 1, "병합후삭제": 2, "삭제금지": 3}.get(x["class"], 4),
            -x["age_days"]
        )),
        "protected_count": len(protected_paths),
    }

    if args.orphans:
        orphans = [c for c in payload["candidates"] if c["class"] == "즉시삭제후보"]
        if args.json:
            print(json.dumps(orphans, ensure_ascii=False))
        else:
            print(f"고아(Orphan) 0순위: {len(orphans)}건")
            for o in orphans[:10]:
                print(f"  {o['path']} (age={o['age_days']}d, calls={o['calls_30d']}, refs={o['refs']})")
        return 0

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        q = payload["quota"]
        print(f"=== Subtraction Quota ({payload['ts']}) ===")
        print(f"hook: raw {q['hook']['raw']} / active {q['hook']['active']} (target {q['hook']['active_target']})")
        print(f"command: {q['command']['raw']} / target {q['command']['target']}")
        print(f"agent: {q['agent']['raw']} / target {q['agent']['target']}")
        print(f"protected: {payload['protected_count']}건")
        print(f"\n=== 정리 후보 ({len(payload['candidates'])}건) ===")
        for c in payload["candidates"][:15]:
            print(f"  [{c['class']}] {c['path']} (age={c['age_days']}d, calls={c['calls_30d']}, refs={c['refs']})")
        if len(payload["candidates"]) > 15:
            print(f"  ... +{len(payload['candidates']) - 15}건")

    return 0


if __name__ == "__main__":
    sys.exit(main())
