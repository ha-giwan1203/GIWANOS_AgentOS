#!/usr/bin/env python3
"""Consolidate clearly named domain backup files without deleting data."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Rule:
    source_dir: str
    dest_dir: str
    pattern: re.Pattern[str]
    reason: str


@dataclass(frozen=True)
class Candidate:
    source: Path
    dest: Path
    rel_source: str
    rel_dest: str
    size_bytes: int
    last_write: str
    reason: str


RULES = [
    Rule(
        source_dir="04_생산계획",
        dest_dir="04_생산계획/_backup/정리_20260529",
        pattern=re.compile(r"(?i)\.bak"),
        reason="생산계획 xlsm 변경 전 백업",
    ),
    Rule(
        source_dir="05_생산실적/조립비정산/01_기준정보",
        dest_dir="05_생산실적/조립비정산/01_기준정보/_backup_20260529",
        pattern=re.compile(r"(?i)(\.bak|_pre_)"),
        reason="기준정보 변경 전 백업 파일명",
    ),
    Rule(
        source_dir="05_생산실적/조립비정산/05월",
        dest_dir="05_생산실적/조립비정산/05월/_local_backup/정리_20260529",
        pattern=re.compile(r"(?i)\.bak"),
        reason="05월 정산 파일 백업",
    ),
    Rule(
        source_dir="05_생산실적/조립비정산/06월",
        dest_dir="05_생산실적/조립비정산/06월/_local_backup/정리_20260529",
        pattern=re.compile(r"(?i)\.bak"),
        reason="06월 작업 파일 백업",
    ),
    Rule(
        source_dir="05_생산실적/조립비정산/04월/04_실적데이터",
        dest_dir="05_생산실적/조립비정산/04월/04_실적데이터/_backup",
        pattern=re.compile(r"(?i)^_backup"),
        reason="04월 실적데이터 백업",
    ),
]


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return path.with_name(f"{stem}_{stamp}{suffix}")


def collect(root: Path) -> list[Candidate]:
    candidates: list[Candidate] = []
    for rule in RULES:
        source_dir = (root / rule.source_dir).resolve()
        dest_dir = (root / rule.dest_dir).resolve()
        if not source_dir.exists():
            continue
        if not is_within(source_dir, root) or not is_within(dest_dir, root):
            raise SystemExit(f"path outside workspace: {source_dir} -> {dest_dir}")
        for item in source_dir.iterdir():
            if not item.is_file():
                continue
            if not rule.pattern.search(item.name):
                continue
            dest = unique_path(dest_dir / item.name)
            stat = item.stat()
            candidates.append(
                Candidate(
                    source=item,
                    dest=dest,
                    rel_source=rel(item, root),
                    rel_dest=rel(dest, root),
                    size_bytes=stat.st_size,
                    last_write=dt.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    reason=rule.reason,
                )
            )
    return sorted(candidates, key=lambda item: item.rel_source)


def write_manifest(path: Path, candidates: list[Candidate], action: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "action",
                "source",
                "destination",
                "size_bytes",
                "size_mb",
                "last_write",
                "reason",
            ],
        )
        writer.writeheader()
        for item in candidates:
            writer.writerow(
                {
                    "action": action,
                    "source": item.rel_source,
                    "destination": item.rel_dest,
                    "size_bytes": item.size_bytes,
                    "size_mb": round(item.size_bytes / 1024 / 1024, 2),
                    "last_write": item.last_write,
                    "reason": item.reason,
                }
            )


def write_report(path: Path, candidates: list[Candidate], action: str) -> None:
    total = sum(item.size_bytes for item in candidates)
    lines = [
        "# 도메인 백업 파일 정리",
        "",
        f"- 기준시각: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} KST",
        f"- action: {action}",
        f"- 대상 파일: {len(candidates):,}개",
        f"- 대상 용량: {total / 1024 / 1024:.2f} MB",
        "- 삭제 없음, 같은 도메인 내부 백업 폴더로만 이동",
        "",
        "## 이동 목록",
        "",
        "| 용량(MB) | 원본 | 이동 후 | 사유 |",
        "|---:|---|---|---|",
    ]
    for item in candidates:
        lines.append(
            f"| {item.size_bytes / 1024 / 1024:.2f} | `{item.rel_source}` | `{item.rel_dest}` | {item.reason} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def execute(candidates: list[Candidate], root: Path) -> None:
    for item in candidates:
        source = item.source.resolve()
        dest = item.dest.resolve()
        if not is_within(source, root) or not is_within(dest, root):
            raise SystemExit(f"path outside workspace: {source} -> {dest}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(dest))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Workspace root")
    parser.add_argument("--output-dir", default="", help="Report directory")
    parser.add_argument("--execute", action="store_true", help="Move files")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output_dir) if args.output_dir else root / "99_임시수집" / f"도메인백업정리_{stamp}"
    if not output_dir.is_absolute():
        output_dir = root / output_dir
    if not is_within(output_dir.resolve(), root):
        raise SystemExit(f"output outside workspace: {output_dir}")

    candidates = collect(root)
    action = "move" if args.execute else "dry-run"
    if args.execute:
        execute(candidates, root)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_manifest(output_dir / "manifest.csv", candidates, action)
    write_report(output_dir / "report.md", candidates, action)

    total = sum(item.size_bytes for item in candidates)
    print(f"ACTION={action}")
    print(f"FILES={len(candidates)}")
    print(f"MB={total / 1024 / 1024:.2f}")
    print(f"REPORT={output_dir / 'report.md'}")
    print(f"MANIFEST={output_dir / 'manifest.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
