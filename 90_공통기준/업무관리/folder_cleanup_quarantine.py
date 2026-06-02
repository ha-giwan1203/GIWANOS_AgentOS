#!/usr/bin/env python3
"""Quarantine low-risk generated cache directories.

This script moves only regenerable cache directories into 99_임시수집 so the
operation is reversible. Business workbooks, backups, Drive sync temp folders,
and node_modules are excluded by default.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import shutil
from dataclasses import dataclass
from pathlib import Path


DEFAULT_CACHE_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".bun-cache",
}

EXCLUDED_PARTS = {
    ".git",
    ".tmp.driveupload",
    ".tmp.drivedownload",
    "node_modules",
}


@dataclass(frozen=True)
class Target:
    source: Path
    rel_path: str
    size_bytes: int
    file_count: int
    reason: str


def is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def dir_stats(path: Path) -> tuple[int, int]:
    total = 0
    files = 0
    for item in path.rglob("*"):
        if item.is_file():
            try:
                total += item.stat().st_size
                files += 1
            except OSError:
                continue
    return total, files


def should_skip(path: Path, root: Path) -> bool:
    rel_parts = path.relative_to(root).parts
    if any(part in EXCLUDED_PARTS for part in rel_parts):
        return True
    return any(part.startswith("폴더정리_격리_") for part in rel_parts)


def collect_targets(root: Path, names: set[str]) -> list[Target]:
    raw: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_dir():
            continue
        if path.name not in names:
            continue
        if should_skip(path, root):
            continue
        raw.append(path)

    selected: list[Path] = []
    for path in sorted(raw, key=lambda p: len(p.parts)):
        if any(is_within(path, parent) for parent in selected):
            continue
        selected.append(path)

    targets: list[Target] = []
    for path in selected:
        size, files = dir_stats(path)
        targets.append(
            Target(
                source=path,
                rel_path=path.relative_to(root).as_posix(),
                size_bytes=size,
                file_count=files,
                reason=f"regenerable cache directory: {path.name}",
            )
        )
    return sorted(targets, key=lambda item: (-item.size_bytes, item.rel_path))


def unique_dest(base: Path, rel_path: str) -> Path:
    dest = base / rel_path
    if not dest.exists():
        return dest
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return dest.with_name(dest.name + f"_{stamp}")


def write_manifest(manifest: Path, targets: list[Target], action: str) -> None:
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "action",
                "rel_path",
                "size_bytes",
                "size_mb",
                "file_count",
                "reason",
            ],
        )
        writer.writeheader()
        for item in targets:
            writer.writerow(
                {
                    "action": action,
                    "rel_path": item.rel_path,
                    "size_bytes": item.size_bytes,
                    "size_mb": round(item.size_bytes / 1024 / 1024, 2),
                    "file_count": item.file_count,
                    "reason": item.reason,
                }
            )


def quarantine(root: Path, targets: list[Target], dest_root: Path, execute: bool) -> list[Target]:
    moved: list[Target] = []
    root = root.resolve()
    dest_root = dest_root.resolve()
    if not is_within(dest_root, root):
        raise SystemExit(f"destination outside workspace: {dest_root}")
    dest_root.mkdir(parents=True, exist_ok=True)

    for item in targets:
        source = item.source.resolve()
        if not is_within(source, root):
            raise SystemExit(f"source outside workspace: {source}")
        if not source.exists():
            continue
        dest = unique_dest(dest_root, item.rel_path)
        if not is_within(dest.resolve(), dest_root):
            raise SystemExit(f"destination escaped quarantine root: {dest}")
        if execute:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(dest))
        moved.append(item)
    return moved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Workspace root")
    parser.add_argument("--output-dir", default="", help="Quarantine directory")
    parser.add_argument("--execute", action="store_true", help="Actually move files")
    parser.add_argument(
        "--include-node-modules",
        action="store_true",
        help="Also quarantine node_modules directories",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    names = set(DEFAULT_CACHE_DIRS)
    if args.include_node_modules:
        names.add("node_modules")
        EXCLUDED_PARTS.discard("node_modules")

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_root = Path(args.output_dir) if args.output_dir else root / "99_임시수집" / f"폴더정리_격리_{stamp}"
    if not dest_root.is_absolute():
        dest_root = root / dest_root

    targets = collect_targets(root, names)
    action = "move" if args.execute else "dry-run"
    moved = quarantine(root, targets, dest_root, execute=args.execute)
    manifest = dest_root / "manifest.csv"
    write_manifest(manifest, moved, action)

    total_size = sum(item.size_bytes for item in moved)
    total_files = sum(item.file_count for item in moved)
    print(f"ACTION={action}")
    print(f"TARGETS={len(moved)}")
    print(f"FILES={total_files}")
    print(f"MB={total_size / 1024 / 1024:.2f}")
    print(f"QUARANTINE={dest_root}")
    print(f"MANIFEST={manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
