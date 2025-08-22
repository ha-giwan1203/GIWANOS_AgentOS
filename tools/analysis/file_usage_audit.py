# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


# ---------------------------
# 설정/경로 로딩 (하드코딩 금지)
# ---------------------------
def _root() -> Path:
    root = os.getenv("VELOS_ROOT")
    if root and Path(root).is_dir():
        return Path(root)
    # settings.yaml에서 base_dir 읽기(없어도 진행)
    sett = os.getenv("VELOS_SETTINGS") or str(Path("C:\giwanos/configs/settings.yaml"))
    try:
        import yaml  # type: ignore

        y = yaml.safe_load(Path(sett).read_text(encoding="utf-8"))
        base = (y or {}).get("paths", {}).get("base_dir")
        if base and Path(base).is_dir():
            return Path(base)
    except Exception:
        pass
    return Path("C:\giwanos") if Path("C:\giwanos").is_dir() else Path.cwd()


ROOT = _root()

PATHS = {
    "reports": ROOT / "data" / "reports",
    "logs": ROOT / "data" / "logs",
    "snapshots": ROOT / "data" / "snapshots",
    "memory": ROOT / "data" / "memory",
}

for p in PATHS.values():
    p.mkdir(parents=True, exist_ok=True)

# ---------------------------
# 감사 대상 확정
# ---------------------------
SCAN_DIRS = [
    ROOT / "scripts",
    ROOT / "modules",
    ROOT / "tools",
    ROOT / "interface",
    ROOT / "configs",
    ROOT / "docs",
    ROOT / "data",
    ROOT / "vector_cache",
    ROOT / "fonts",
]

# Python/PS/Config/MD 등 전반 스캔
CODE_EXT = {
    ".py",
    ".ps1",
    ".cmd",
    ".bat",
    ".psm1",
    ".json",
    ".yaml",
    ".yml",
    ".md",
    ".txt",
    ".css",
    ".js",
    ".ts",
}


# ---------------------------
# 유틸
# ---------------------------
def sh(cmd: List[str]) -> Tuple[int, str]:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=False)
        return 0, out.decode("utf-8", errors="ignore")
    except subprocess.CalledProcessError as e:
        return e.returncode, e.output.decode("utf-8", errors="ignore")


def is_git_repo(path: Path) -> bool:
    try:
        code, _ = sh(["git", "-C", str(path), "rev-parse", "--is-inside-work-tree"])
        return code == 0
    except Exception:
        return False


def git_last_commit(path: Path) -> Optional[str]:
    try:
        if not is_git_repo(ROOT):
            return None
        code, out = sh(["git", "-C", str(ROOT), "log", "-1", "--pretty=%ci", "--", str(path)])
        return out.strip() if code == 0 and out.strip() else None
    except Exception:
        return None


def file_hash(path: Path, limit: int = 2 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            h.update(f.read(limit))
        return h.hexdigest()
    except Exception:
        return ""


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


# ---------------------------
# 정적 분석: import/참조 그래프
# ---------------------------
py_import_re = re.compile(r"^\s*(?:from\s+([\w\.\_]+)\s+import|import\s+([\w\.\_]+))", re.MULTILINE)
path_hint_re = re.compile(r'["\']([A-Za-z]:\\\\[^"\']+|\/mnt\/data\/[^"\']+|C:\/[^"\']+)["\']')


def scan_files() -> List[Path]:
    targets: List[Path] = []
    for d in SCAN_DIRS:
        if not d.exists():
            continue
        # 최대 100개 파일로 제한
        count = 0
        for p in d.rglob("*"):
            if count >= 100:
                break
            if p.is_file() and (
                p.suffix.lower() in CODE_EXT
                or p.suffix.lower() == ""
                and p.name.lower().endswith(".md")
            ):
                targets.append(p)
                count += 1
    return targets


def analyze_static(files: List[Path]) -> Dict:
    py_files = [p for p in files if p.suffix.lower() == ".py"]
    imports: Dict[str, Set[str]] = {}
    path_refs: Dict[str, Set[str]] = {}
    for p in py_files:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            text = ""
        imps: Set[str] = set()
        for m in py_import_re.finditer(text):
            pkg = m.group(1) or m.group(2)
            if pkg:
                imps.add(pkg.split(".")[0])
        imports[str(p.relative_to(ROOT))] = imps

        refs = set()
        for m in path_hint_re.finditer(text):
            refs.add(m.group(1))
        path_refs[str(p.relative_to(ROOT))] = refs

    return {"imports": imports, "path_refs": path_refs}


# ---------------------------
# 동적 단서: 로그/리포트/세션 접근 흔적
# ---------------------------
def dynamic_hints() -> Dict[str, List[str]]:
    hits: Dict[str, List[str]] = {}
    log_paths = []
    for pat in ["*.json", "*.jsonl", "*.log", "*.md", "*.txt"]:
        log_paths += list(PATHS["logs"].glob(pat))
        log_paths += list(PATHS["reports"].glob(pat))
        log_paths += list(PATHS["memory"].glob(pat))

    for lp in log_paths:
        try:
            txt = lp.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for p in re.findall(r"(C:\\giwanos\\[A-Za-z0-9_\-\\\.]+)", txt):
            hits.setdefault(str(lp.relative_to(ROOT)), []).append(p)
    return hits


# ---------------------------
# 분류 로직
# ---------------------------
ENTRY_POINTS = {
    "scripts/run_giwanos_master_loop.py",
    "interface/velos_dashboard.py",
    "tools/notifications/system_alert_notifier.py",
    "modules/report/generate_pdf_report.py",
}


def load_feature_whitelist() -> Dict:
    """기능 화이트리스트 로드"""
    whitelist_path = ROOT / "configs" / "feature_manifest.yaml"
    if not whitelist_path.exists():
        return {"features": [], "global": {"exclude_patterns": []}}

    try:
        import yaml

        with open(whitelist_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {"features": [], "global": {"exclude_patterns": []}}
    except Exception:
        return {"features": [], "global": {"exclude_patterns": []}}


def is_whitelisted(file_path: str, whitelist: Dict) -> bool:
    """파일이 화이트리스트에 포함되는지 확인"""
    from fnmatch import fnmatch

    # 글로벌 제외 패턴 확인
    for pattern in whitelist.get("global", {}).get("exclude_patterns", []):
        if fnmatch(file_path, pattern):
            return True

    # 기능별 화이트리스트 확인
    for feature in whitelist.get("features", []):
        if not feature.get("enabled", True):
            continue
        for pattern in feature.get("keep_patterns", []):
            if fnmatch(file_path, pattern):
                return True

    return False


def classify(files: List[Path], static_info: Dict, dyn: Dict[str, List[str]]) -> Dict:
    # 화이트리스트 로드
    whitelist = load_feature_whitelist()

    # 기준 1: 엔트리포인트가 import하는 연쇄
    imports = static_info["imports"]  # file -> set(pkg)
    file_by_module = {Path(f).with_suffix("").name: f for f in imports.keys()}

    # 정적 그래프 걸어 활성 후보 만들기
    active_candidates: Set[str] = set()

    def mark_active(start_file: str):
        if start_file in active_candidates:
            return
        active_candidates.add(start_file)

    for ep in ENTRY_POINTS:
        if ep in imports:
            mark_active(ep)

    # 그냥 import 흔적이 있으면 넓게 포함
    for f, imps in imports.items():
        if imps and f not in active_candidates:
            # 보수적으로 포함
            active_candidates.add(f)

    # 기준 2: 동적 로그에 등장하면 런타임 접근 흔적
    runtime_access: Set[str] = set()
    for log, paths in dyn.items():
        for full in paths:
            try:
                rp = str(Path(full).relative_to(ROOT))
                runtime_access.add(rp)
            except Exception:
                pass

    # 기준 3: Git 최근 커밋 (비활성화 - 시간 오래 걸림)
    recent_touch: Set[str] = set()
    # if is_git_repo(ROOT):
    #     for p in files:
    #         last = git_last_commit(p)
    #         if last:
    #             # 최근 90일 커밋은 살아있다고 본다
    #             recent_touch.add(str(p.relative_to(ROOT)))

    # 종합 분류
    res = {}
    for p in files:
        rel = str(p.relative_to(ROOT))
        meta = {
            "size": p.stat().st_size if p.exists() else 0,
            "mtime": (
                time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(p.stat().st_mtime))
                if p.exists()
                else None
            ),
            "hash": file_hash(p),
            "git_last_commit": git_last_commit(p),
            "kind": p.suffix.lower() or "other",
            "in_static_graph": rel in imports,
            "in_runtime_logs": rel in runtime_access,
            "recent_git_touch": rel in recent_touch,
            "whitelisted": is_whitelisted(rel, whitelist),
            "category": "unknown",
        }

        # 화이트리스트 우선 적용
        if meta["whitelisted"]:
            meta["category"] = "whitelist_protected"
        # 규칙 기반 카테고리
        elif rel in ENTRY_POINTS:
            meta["category"] = "core_active"
        elif meta["in_runtime_logs"]:
            meta["category"] = "runtime_accessed"
        elif meta["in_static_graph"]:
            meta["category"] = "statically_referenced"
        elif p.parent.match("data/snapshots*"):
            meta["category"] = "snapshot_generated"
        elif meta["recent_git_touch"]:
            meta["category"] = "recently_touched"
        else:
            meta["category"] = "orphan_candidate"

        res[rel] = meta

    return res


# ---------------------------
# 리포트 저장
# ---------------------------
def save_report(rows: Dict) -> Tuple[Path, Path]:
    PATHS["reports"].mkdir(parents=True, exist_ok=True)
    js = {
        "generated_at": now_iso(),
        "root": str(ROOT),
        "summary": {
            "total": len(rows),
            "whitelist_protected": sum(
                1 for v in rows.values() if v["category"] == "whitelist_protected"
            ),
            "core_active": sum(1 for v in rows.values() if v["category"] == "core_active"),
            "runtime_accessed": sum(
                1 for v in rows.values() if v["category"] == "runtime_accessed"
            ),
            "statically_referenced": sum(
                1 for v in rows.values() if v["category"] == "statically_referenced"
            ),
            "recently_touched": sum(
                1 for v in rows.values() if v["category"] == "recently_touched"
            ),
            "snapshot_generated": sum(
                1 for v in rows.values() if v["category"] == "snapshot_generated"
            ),
            "orphan_candidate": sum(
                1 for v in rows.values() if v["category"] == "orphan_candidate"
            ),
        },
        "files": rows,
    }
    out_json = PATHS["reports"] / "file_usage_report.json"
    out_md = PATHS["reports"] / "file_usage_report.md"

    out_json.write_text(json.dumps(js, ensure_ascii=False, indent=2), encoding="utf-8")

    # Markdown 요약
    def line(cat):
        return f"- **{cat}**: {js['summary'][cat]}"

    md = [
        f"# VELOS 파일 사용성 감사 보고서",
        f"- 생성 시각: {js['generated_at']}",
        f"- 루트: `{js['root']}`",
        "## 요약",
        line("whitelist_protected"),
        line("core_active"),
        line("runtime_accessed"),
        line("statically_referenced"),
        line("recently_touched"),
        line("snapshot_generated"),
        line("orphan_candidate"),
        "",
        "## Orphan 후보 상위 50개",
    ]
    # 크기/최근 수정 오래된 순 정렬
    orphans = [(k, v) for k, v in rows.items() if v["category"] == "orphan_candidate"]
    orphans.sort(key=lambda kv: (kv[1]["mtime"] or "", kv[1]["size"]), reverse=False)
    for k, v in orphans[:50]:
        md.append(
            f"- `{k}` | mtime={v['mtime']} | size={v['size']} | last_commit={v['git_last_commit'] or 'N/A'}"
        )

    out_md.write_text("\n".join(md), encoding="utf-8")
    return out_json, out_md


# ---------------------------
# 메인/자가검증
# ---------------------------
def main() -> int:
    files = scan_files()
    static_info = analyze_static(files)
    dyn = dynamic_hints()
    rows = classify(files, static_info, dyn)
    j, m = save_report(rows)

    # 간단 검증
    assert j.exists() and j.stat().st_size > 0, "JSON 리포트 생성 실패"
    assert m.exists() and m.stat().st_size > 0, "MD 리포트 생성 실패"

    # 표준 출력 요약
    s = json.loads(j.read_text(encoding="utf-8"))["summary"]
    print("[report]", j)
    print("[summary]", s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
