# [ACTIVE] VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

from __future__ import annotations
import os, sys, json, time
from pathlib import Path
from typing import Dict, List, Set


def _root() -> Path:
    root = os.getenv("VELOS_ROOT")
    if root and Path(root).is_dir():
        return Path(root)
    sett = os.getenv("VELOS_SETTINGS") or "/workspace/configs/settings.yaml"
    try:
        import yaml  # type: ignore
        if Path(sett).exists():
            with open(sett, 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f)
                if cfg and cfg.get("base_dir"):
                    return Path(cfg["base_dir"])
    except Exception:
        pass
    return Path("/workspace") if Path("/workspace").is_dir() else Path.cwd()


ROOT = _root()
TRACE_DIR = ROOT / "data" / "logs" / "runtime_trace"
CONF = ROOT / "configs" / "feature_manifest.yaml"
REPORTS = ROOT / "data" / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


def load_manifest() -> Dict:
    if not CONF.exists():
        return {"features": []}
    import yaml  # type: ignore
    return yaml.safe_load(CONF.read_text(encoding="utf-8")) or {"features": []}


def save_manifest(data: Dict) -> None:
    import yaml  # type: ignore
    backup = CONF.with_suffix(".bak.yaml")
    if CONF.exists():
        backup.write_text(CONF.read_text(encoding="utf-8"), encoding="utf-8")
    CONF.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def read_trace_used_paths(days: int = 30) -> Set[str]:
    used: Set[str] = set()
    if not TRACE_DIR.exists():
        return used
    cutoff = time.time() - days * 86400
    for path in TRACE_DIR.glob("trace_*.jsonl"):
        if path.stat().st_mtime < cutoff:
            continue
        for ln in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                rec = json.loads(ln)
            except Exception:
                continue
            if rec.get("type") in {"import", "open"}:
                f = rec.get("file")
                if isinstance(f, str) and f and not f.startswith("N/A"):
                    used.add(f)
    return used


def to_patterns(paths: Set[str]) -> List[str]:
    # 너무 세밀하면 리스트가 길어진다. 상위 2뎁스로 뭉쳐준다.
    buckets: Set[str] = set()
    for rel in paths:
        parts = Path(rel).parts
        if len(parts) >= 2:
            buckets.add("/".join(parts[:2]) + "/**")
        elif len(parts) == 1:
            buckets.add(parts[0])
    return sorted(buckets)


def ensure_feature(manifest: Dict, name: str) -> Dict:
    for f in manifest.get("features", []):
        if f.get("name") == name:
            return f
    newf = {"name": name, "enabled": True, "keep_patterns": []}
    manifest.setdefault("features", []).append(newf)
    return newf


def merge_patterns(dst: List[str], add: List[str]) -> List[str]:
    s = set(dst)
    for p in add:
        s.add(p)
    out = sorted(s)
    return out


def main(argv=None) -> int:
    used = read_trace_used_paths(days=90)
    pats = to_patterns(used)

    manifest = load_manifest()
    auto = ensure_feature(manifest, "auto_runtime_trace")
    before = set(auto.get("keep_patterns") or [])
    auto["keep_patterns"] = merge_patterns(list(before), pats)

    save_manifest(manifest)

    # 리포트
    rep = {
        "generated_at": _now(),
        "used_paths_count": len(used),
        "new_patterns_added": sorted(set(pats) - before),
        "manifest_path": str(CONF),
    }
    outj = REPORTS / "manifest_sync_report.json"
    outm = REPORTS / "manifest_sync_report.md"
    outj.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    # 신규 패턴 목록 생성
    new_patterns_text = []
    if rep["new_patterns_added"]:
        for p in rep["new_patterns_added"]:
            new_patterns_text.append(f"- `{p}`")
    else:
        new_patterns_text.append("- (없음)")

    outm.write_text(
        "\n".join([
            "# Manifest 동기화 보고서",
            f"- 생성: {rep['generated_at']}",
            f"- 추출된 경로 개수: {rep['used_paths_count']}",
            "## 신규 패턴",
            *new_patterns_text,
            f"\nManifest: `{rep['manifest_path']}`"
        ]),
        encoding="utf-8"
    )
    print("[OK] manifest synced", outj)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
