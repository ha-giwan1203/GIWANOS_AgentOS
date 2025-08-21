# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


# ===== 경로/설정 로딩 =====
def _root() -> Path:
    root = os.getenv("VELOS_ROOT")
    if root and Path(root).is_dir():
        return Path(root)
    sett = os.getenv("VELOS_SETTINGS") or "/home/user/webapp/configs/settings.yaml"
    try:
        import yaml  # type: ignore

        y = yaml.safe_load(Path(sett).read_text(encoding="utf-8"))
        base = (y or {}).get("paths", {}).get("base_dir")
        if base and Path(base).is_dir():
            return Path(base)
    except Exception:
        pass
    return Path("/home/user/webapp") if Path("/home/user/webapp").is_dir() else Path.cwd()


ROOT = _root()
REPORTS = ROOT / "data" / "reports"
LOGS = ROOT / "data" / "logs"
MEMORY = ROOT / "data" / "memory"

for p in (REPORTS, LOGS, MEMORY):
    p.mkdir(parents=True, exist_ok=True)

# ===== 스캔 대상/확장자 =====
SCAN_DIRS = [
    ROOT / d
    for d in [
        "scripts",
        "modules",
        "tools",
        "interface",
        "configs",
        "docs",
        "data",
        "vector_cache",
        "fonts",
    ]
]
CODE_EXT = {
    ".py",
    ".ps1",
    ".psm1",
    ".cmd",
    ".bat",
    ".json",
    ".yaml",
    ".yml",
    ".md",
    ".txt",
    ".css",
    ".js",
    ".ts",
    ".ini",
    ".toml",
}


# ===== 유틸 =====
def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


def sh(cmd: List[str]) -> Tuple[int, str]:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return 0, out.decode("utf-8", errors="ignore")
    except subprocess.CalledProcessError as e:
        return e.returncode, e.output.decode("utf-8", errors="ignore")
    except Exception as e:
        return 1, str(e)


def is_git_repo(path: Path) -> bool:
    code, _ = sh(["git", "-C", str(path), "rev-parse", "--is-inside-work-tree"])
    return code == 0


def git_last_commit(path: Path) -> Optional[str]:
    if not is_git_repo(ROOT):
        return None
    code, out = sh(["git", "-C", str(ROOT), "log", "-1", "--pretty=%ci", "--", str(path)])
    return out.strip() if code == 0 and out.strip() else None


def file_hash(path: Path, limit: int = 2 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            h.update(f.read(limit))
        return h.hexdigest()
    except Exception:
        return ""


# ===== Manifest 로딩 =====
def load_manifest() -> List[Dict]:
    mf = ROOT / "configs" / "feature_manifest.yaml"
    if not mf.exists():
        return []
    try:
        import yaml  # type: ignore

        y = yaml.safe_load(mf.read_text(encoding="utf-8")) or {}
        return [f for f in (y.get("features") or []) if f.get("enabled")]
    except Exception:
        return []


def match_manifest_keep(rel: str, manifest: List[Dict]) -> Optional[str]:
    for feat in manifest:
        for pat in feat.get("keep_patterns") or []:
            if fnmatch.fnmatch(rel.replace("\\", "/"), pat):
                return feat.get("name") or "manifest"
    return None


# ===== 파일 스캔/정적 분석 =====
py_import_re = re.compile(r"^\s*(?:from\s+([\w\.\_]+)\s+import|import\s+([\w\.\_]+))", re.MULTILINE)
path_hint_re = re.compile(r'["\'](C:\\\\[^"\']+|C:/[^"\']+|/mnt/data/[^"\']+)["\']')


def scan_files() -> List[Path]:
    out: List[Path] = []
    for d in SCAN_DIRS:
        if not d.exists():
            continue
        for p in d.rglob("*"):
            if p.is_file() and (p.suffix.lower() in CODE_EXT):
                out.append(p)
    return out


def analyze_static(files: List[Path]) -> Dict:
    imports: Dict[str, Set[str]] = {}
    path_refs: Dict[str, Set[str]] = {}
    for p in files:
        if p.suffix.lower() != ".py":
            continue
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


# ===== 동적 흔적(로그/리포트/메모리) =====
def dynamic_hints() -> Dict[str, List[str]]:
    hits: Dict[str, List[str]] = {}
    pools = []
    for base in (LOGS, REPORTS, MEMORY):
        if base.exists():
            pools.extend(list(base.rglob("*.json")))
            pools.extend(list(base.rglob("*.jsonl")))
            pools.extend(list(base.rglob("*.log")))
            pools.extend(list(base.rglob("*.md")))
            pools.extend(list(base.rglob("*.txt")))
    for lp in pools:
        try:
            txt = lp.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for full in re.findall(r"(C:\\giwanos\\[A-Za-z0-9_\-\\\.]+)", txt):
            try:
                rel = str(Path(full).relative_to(ROOT))
                hits.setdefault(str(lp.relative_to(ROOT)), []).append(rel)
            except Exception:
                pass
    return hits


# ===== 스케줄러/태스크/툴링 참조 추출 =====
def scheduled_task_paths() -> Set[str]:
    out: Set[str] = set()
    if platform.system().lower().startswith("win"):
        code, txt = sh(["schtasks", "/query", "/fo", "LIST", "/v"])
        if code == 0:
            for line in txt.splitlines():
                if "Task To Run" in line or "작업 실행" in line:
                    # 경로 추출
                    m = re.findall(r'(C:\\[^"]+)', line)
                    for p in m:
                        try:
                            rel = str(Path(p).relative_to(ROOT))
                            out.add(rel)
                        except Exception:
                            pass
    # VSCode tasks.json 힌트
    tasks = ROOT / ".vscode" / "tasks.json"
    if tasks.exists():
        try:
            j = json.loads(tasks.read_text(encoding="utf-8"))
            blob = json.dumps(j, ensure_ascii=False)
            for m in re.findall(r"(C:\\\\giwanos\\\\[A-Za-z0-9_\-\\\.]+)", blob):
                try:
                    rel = str(Path(m.replace("\\\\", "\\")).relative_to(ROOT))
                    out.add(rel)
                except Exception:
                    pass
        except Exception:
            pass
    return out


# ===== 분류/스코어 =====
ENTRY_POINTS = {
    "scripts/run_giwanos_master_loop.py",
    "interface/velos_dashboard.py",
    "tools/notifications/system_alert_notifier.py",
    "modules/report/generate_pdf_report.py",
}


def days_ago(ts: float) -> int:
    return int((time.time() - ts) / 86400)


def classify(
    files: List[Path], static_info: Dict, dyn_hits: Dict[str, List[str]], manifest: List[Dict]
) -> Dict:
    imports = static_info["imports"]
    sched_refs = scheduled_task_paths()

    dyn_refs: Set[str] = set()
    for _, rels in dyn_hits.items():
        for r in rels:
            dyn_refs.add(r)

    rows: Dict[str, Dict] = {}
    for p in files:
        rel = str(p.relative_to(ROOT))
        stat = p.stat()
        size = stat.st_size
        mtime_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(stat.st_mtime))
        mday = days_ago(stat.st_mtime)

        manifest_name = match_manifest_keep(rel, manifest)
        in_import_map = rel in imports
        in_dyn_logs = rel in dyn_refs
        in_sched = rel in sched_refs
        in_entry = rel in ENTRY_POINTS
        git_when = git_last_commit(p)
        recent_git = False
        if git_when:
            recent_git = True  # 보수적으로 '최근 터치'로 인정

        # 위험도는 "지워도 될 가능성" 점수. 낮을수록 안전(KEEP), 높을수록 고아 후보.
        risk = 100
        reasons: List[str] = []

        # 보호 신호들: 크게 깎음
        if manifest_name:
            risk -= 100
            reasons.append(f"manifest_keep:{manifest_name}")
        if in_entry:
            risk -= 80
            reasons.append("entry_point")
        if in_sched:
            risk -= 60
            reasons.append("scheduled_task_ref")
        if in_import_map:
            risk -= 40
            reasons.append("statically_referenced")
        if in_dyn_logs:
            risk -= 30
            reasons.append("runtime_log_reference")
        if recent_git:
            risk -= 20
            reasons.append("recent_git_commit")
        if mday <= 180:
            risk -= 10
            reasons.append("recent_mtime<=180d")

        # 위치 기반 가중치(코어 영역이면 더 보호)
        if rel.startswith(
            ("scripts/", "modules/core/", "interface/", "tools/notifications/", "modules/report/")
        ):
            risk -= 10
            reasons.append("core_dir_bonus")

        # 최소 보수 가드: 절대 음수 방어
        if risk < 0:
            risk = 0

        # 최종 라벨
        if risk <= 10:
            label = "KEEP_STRICT"
        elif risk <= 25:
            label = "KEEP"
        elif risk <= 50:
            label = "REVIEW"
        else:
            # 고아 후보도 '1년 넘게 안 만짐' + '크기 작음(<=64KB)'일 때만 표시
            label = (
                "QUARANTINE_CANDIDATE"
                if (
                    mday > 365
                    and size <= 65536
                    and not manifest_name
                    and not in_sched
                    and not in_entry
                    and not in_import_map
                    and not in_dyn_logs
                )
                else "REVIEW"
            )

        rows[rel] = {
            "label": label,
            "risk": risk,
            "reasons": reasons,
            "size": size,
            "mtime": mtime_iso,
            "hash": file_hash(p),
            "git_last_commit": git_when or "N/A",
        }
    return rows


# ===== 리포트 저장 =====
def save_report(rows: Dict) -> Tuple[Path, Path]:
    REPORTS.mkdir(parents=True, exist_ok=True)
    out_json = REPORTS / "file_usage_risk_report.json"
    out_md = REPORTS / "file_usage_risk_report.md"

    summary = {
        k: sum(1 for v in rows.values() if v["label"] == k)
        for k in ["KEEP_STRICT", "KEEP", "REVIEW", "QUARANTINE_CANDIDATE"]
    }
    js = {
        "generated_at": now_iso(),
        "root": str(ROOT),
        "summary": summary,
        "files": rows,
        "deletion_guard": os.getenv("VELOS_DELETION_GUARD", "paranoid"),
    }
    out_json.write_text(json.dumps(js, ensure_ascii=False, indent=2), encoding="utf-8")

    # MD
    parts = [
        f"# VELOS 파일 사용성 리스크 보고서",
        f"- 생성: {js['generated_at']}",
        f"- 루트: `{js['root']}`",
        f"- 가드: `{js['deletion_guard']}`",
        "## 요약",
        f"- KEEP_STRICT: {summary['KEEP_STRICT']}",
        f"- KEEP: {summary['KEEP']}",
        f"- REVIEW: {summary['REVIEW']}",
        f"- QUARANTINE_CANDIDATE: {summary['QUARANTINE_CANDIDATE']}",
        "",
        "## 고아 후보(Q)**주의: 즉시 삭제 금지**",
    ]
    # 고아 후보 정렬: 오래된 순
    qs = [(k, v) for k, v in rows.items() if v["label"] == "QUARANTINE_CANDIDATE"]
    qs.sort(key=lambda kv: kv[1]["mtime"])
    for k, v in qs[:100]:
        r = ",".join(v["reasons"])
        parts.append(f"- `{k}` | risk={v['risk']} | mtime={v['mtime']} | reasons={r}")

    out_md.write_text("\n".join(parts), encoding="utf-8")
    return out_json, out_md


# ===== 메인 =====
def main() -> int:
    files = scan_files()
    static_info = analyze_static(files)
    dyn_hits = dynamic_hints()
    manifest = load_manifest()
    rows = classify(files, static_info, dyn_hits, manifest)
    j, m = save_report(rows)
    # 간단 검증
    assert j.exists() and j.stat().st_size > 0
    assert m.exists() and m.stat().st_size > 0
    print("[report]", j)
    print("[report]", m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
