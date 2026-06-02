#!/usr/bin/env python3
"""Audit workspace clutter without moving or deleting files.

The script classifies generated files, backups, caches, and root-level drift by
path metadata only. It is intentionally read-only except for writing reports.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT_ALLOW_DIRS = {
    ".claude",
    ".codex",
    ".git",
    "01_인사근태",
    "02_급여단가",
    "03_품번관리",
    "04_생산계획",
    "05_생산실적",
    "06_생산관리",
    "07_라인정지비용",
    "08_공정개선이슈",
    "09_외주발주납품",
    "10_라인배치",
    "90_공통기준",
    "98_아카이브",
    "99_임시수집",
}

ROOT_ALLOW_FILES = {
    ".claudeignore",
    ".gdignore",
    ".gitignore",
    ".watch.lock",
    "AGENTS.md",
    "CLAUDE.md",
    "README.md",
}

CACHE_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".bun-cache",
    "dist",
    "build",
}

RUNTIME_DEPENDENCY_DIR_NAMES = {
    "node_modules",
}

BACKUP_RE = re.compile(
    r"(?i)(\.bak($|_)|bak_|backup|_backup|(^|[_. -])old($|[_. -])|copy|before|"
    r"(^pre_)|_pre_|복사|복사본|백업|(^|[_. -])임시($|[_. -])|"
    r"(^|[_. -])temp($|[_. -])|\.tmp$)"
)
TEMP_RE = re.compile(r"(?i)(^~\$|\.tmp$|\.temp$|\.swp$|\.swo$|~$)")


@dataclass(frozen=True)
class Finding:
    bucket: str
    severity: str
    action: str
    rel_path: str
    kind: str
    size_bytes: int
    last_write: str
    reason: str


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def git_lines(root: Path, *args: str) -> set[str]:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return set()
    if result.returncode != 0:
        return set()
    return {line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()}


def mtime(path: Path) -> str:
    try:
        return dt.datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    except OSError:
        return ""


def file_size(path: Path) -> int:
    try:
        return path.stat().st_size if path.is_file() else 0
    except OSError:
        return 0


def dir_size(path: Path) -> tuple[int, int]:
    total = 0
    files = 0
    for item in path.rglob("*"):
        if ".git" in item.parts:
            continue
        if item.is_file():
            total += file_size(item)
            files += 1
    return total, files


def skip_scan_path(path: Path) -> bool:
    if ".git" in path.parts:
        return True
    if ".claude" in path.parts or ".codex" in path.parts:
        return True
    if "98_아카이브" in path.parts:
        return True
    if any(
        part in {"_backup", "_local_backup", "백업"}
        or part.startswith("_backup_")
        or part.startswith("정리_")
        for part in path.parts
    ):
        return True
    if "03_품번관리" in path.parts and "초물관리" in path.parts and "_output" in path.parts:
        return True
    if "node_modules" in path.parts:
        return not (path.name == "node_modules" and path.parts.count("node_modules") == 1)
    return any(
        part.startswith("폴더정리_격리_") or part.startswith("드라이브임시_격리_")
        or part.startswith("폴더정리_20260529")
        for part in path.parts
    )


def is_organized_backup(path: Path) -> bool:
    backup_markers = {"_backup", "_local_backup", "백업"}
    if "98_아카이브" in path.parts:
        return True
    for parent in path.parents:
        name = parent.name
        if name in backup_markers or name.startswith("_backup_") or name.startswith("정리_"):
            return True
    return False


def classify(root: Path) -> list[Finding]:
    ignored = git_lines(root, "ls-files", "--ignored", "--exclude-standard", "--others")
    untracked = git_lines(root, "ls-files", "--others", "--exclude-standard")
    findings: list[Finding] = []
    seen: set[tuple[str, str]] = set()
    cache_roots: set[Path] = set()

    def add(
        path: Path,
        bucket: str,
        severity: str,
        action: str,
        reason: str,
        kind: str | None = None,
        size_override: int | None = None,
    ) -> None:
        rel_path = rel(path, root)
        key = (bucket, rel_path)
        if key in seen:
            return
        seen.add(key)
        actual_kind = kind or ("dir" if path.is_dir() else "file")
        size = size_override if size_override is not None else file_size(path)
        findings.append(
            Finding(
                bucket=bucket,
                severity=severity,
                action=action,
                rel_path=rel_path,
                kind=actual_kind,
                size_bytes=size,
                last_write=mtime(path),
                reason=reason,
            )
        )

    for child in root.iterdir():
        name = child.name
        if child.is_dir() and name not in ROOT_ALLOW_DIRS:
            size, files = dir_size(child)
            add(
                child,
                "root_drift",
                "review",
                "표준 대분류 또는 99_임시수집/98_아카이브로 이동 검토",
                f"루트 비표준 폴더, 하위 파일 {files}개",
                size_override=size,
            )
        elif child.is_file() and name not in ROOT_ALLOW_FILES:
            add(
                child,
                "root_drift",
                "review",
                "업무 성격에 맞는 대분류 폴더로 이동 검토",
                "루트 비표준 파일",
            )

    for drive_tmp in (root / ".tmp.driveupload", root / ".tmp.drivedownload"):
        if drive_tmp.exists():
            size, files = dir_size(drive_tmp)
            action = "Google Drive 동기화 중지 확인 후 삭제 또는 격리"
            severity = "safe-after-sync-check" if files else "safe"
            add(
                drive_tmp,
                "drive_temp",
                severity,
                action,
                f"Google Drive 임시 폴더, 하위 파일 {files}개",
                size_override=size,
            )

    for path in root.rglob("*"):
        if skip_scan_path(path):
            continue
        rel_path = rel(path, root)
        name = path.name

        if path.is_dir() and name in RUNTIME_DEPENDENCY_DIR_NAMES:
            size, files = dir_size(path)
            add(
                path,
                "runtime_dependency",
                "review",
                "package manager 재설치 경로 확인 후 별도 정리",
                f"런타임 의존성 폴더, 하위 파일 {files}개",
                size_override=size,
            )
            continue

        if path.is_dir() and name in CACHE_DIR_NAMES:
            if any(parent in cache_roots for parent in path.parents):
                continue
            cache_roots.add(path)
            size, files = dir_size(path)
            add(
                path,
                "generated_cache",
                "safe",
                "재생성 가능하므로 삭제/격리 가능",
                f"빌드 또는 런타임 캐시, 하위 파일 {files}개",
                size_override=size,
            )
            continue

        if path.is_file():
            if rel_path in untracked:
                add(
                    path,
                    "git_untracked",
                    "review",
                    "추적 필요 여부 결정, 임시 산출물이면 99_임시수집 또는 ignore",
                    "git 미추적 파일",
                )
            if rel_path in ignored:
                add(
                    path,
                    "git_ignored_physical",
                    "review",
                    "보존 필요 없으면 99_임시수집 또는 삭제 후보",
                    "git ignore 대상이지만 실제 디스크에 존재",
                )
            if TEMP_RE.search(name):
                add(
                    path,
                    "temp_file",
                    "safe",
                    "작업 중 파일 아니면 삭제/격리 가능",
                    "임시 파일명 패턴",
                )
            elif BACKUP_RE.search(name):
                if is_organized_backup(path):
                    continue
                severity = "review" if any(part.startswith(("04_", "05_", "06_")) for part in path.parts) else "safe"
                action = "최신 원본 확인 후 월/도메인별 백업 폴더로 합치기"
                add(path, "backup_file", severity, action, "백업/복사/old 파일명 패턴")

    return findings


def write_reports(root: Path, output_dir: Path, findings: list[Finding]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "cleanup_candidates.csv"
    md_path = output_dir / "cleanup_report.md"

    by_bucket = defaultdict(list)
    for item in findings:
        by_bucket[item.bucket].append(item)

    with csv_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "bucket",
                "severity",
                "action",
                "rel_path",
                "kind",
                "size_bytes",
                "size_mb",
                "last_write",
                "reason",
            ],
        )
        writer.writeheader()
        for item in sorted(findings, key=lambda x: (x.bucket, -x.size_bytes, x.rel_path)):
            writer.writerow(
                {
                    "bucket": item.bucket,
                    "severity": item.severity,
                    "action": item.action,
                    "rel_path": item.rel_path,
                    "kind": item.kind,
                    "size_bytes": item.size_bytes,
                    "size_mb": round(item.size_bytes / 1024 / 1024, 2),
                    "last_write": item.last_write,
                    "reason": item.reason,
                }
            )

    total_size = sum(item.size_bytes for item in findings)
    lines = [
        "# 업무리스트 폴더 정리 감사",
        "",
        f"- 기준시각: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} KST",
        f"- 대상: {root}",
        f"- 방식: 파일 내용 미열람, 경로/파일명/크기/수정일/git 상태 기준",
        f"- 후보 건수: {len(findings):,}건",
        f"- 후보 항목 용량: {total_size / 1024 / 1024:.2f} MB",
        "- 주의: bucket별 성격을 보기 위한 항목 합산이며, 같은 파일/폴더가 여러 bucket에 걸치면 중복될 수 있음",
        "",
        "## 요약",
        "",
        "| bucket | 건수 | 용량(MB) | 판단 |",
        "|---|---:|---:|---|",
    ]

    severity_by_bucket: dict[str, Counter[str]] = {}
    for bucket, items in sorted(by_bucket.items()):
        counter = Counter(item.severity for item in items)
        severity_by_bucket[bucket] = counter
        size_mb = sum(item.size_bytes for item in items) / 1024 / 1024
        judgement = ", ".join(f"{k}:{v}" for k, v in sorted(counter.items()))
        lines.append(f"| {bucket} | {len(items):,} | {size_mb:.2f} | {judgement} |")

    lines.extend(
        [
            "",
            "## 실행 기준",
            "",
            "| 구분 | 처리 |",
            "|---|---|",
            "| safe | 삭제/격리 가능하나 현재 스크립트는 이동·삭제 안 함 |",
            "| safe-after-sync-check | Google Drive 동기화 종료 확인 후 처리 |",
            "| review | 원본·참조·업무 영향 확인 전 보류 |",
            "",
            "## 상위 후보",
            "",
        ]
    )

    for bucket, items in sorted(by_bucket.items()):
        lines.extend([f"### {bucket}", "", "| 용량(MB) | 수정일 | 판단 | 경로 |", "|---:|---|---|---|"])
        for item in sorted(items, key=lambda x: (-x.size_bytes, x.rel_path))[:20]:
            lines.append(
                f"| {item.size_bytes / 1024 / 1024:.2f} | {item.last_write} | {item.severity} | `{item.rel_path}` |"
            )
        lines.append("")

    lines.extend(
        [
            "## 3줄 인사이트",
            "",
            "1. 루트 난립보다 ignored 물리 파일과 백업 파일 누적이 더 큰 정리 대상이다.",
            "2. Google Drive 임시 업로드 폴더는 파일 수가 많아 체감 혼잡의 주원인이지만 동기화 상태 확인 전 삭제 금지다.",
            "3. 정산/생산계획 백업은 원본 회복용일 수 있어 월별 백업 폴더로 모으는 방식이 안전하다.",
            "",
            f"- 상세 CSV: `{csv_path.name}`",
        ]
    )

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Workspace root")
    parser.add_argument("--output-dir", default="", help="Report output directory")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output_dir) if args.output_dir else root / "99_임시수집" / f"폴더정리_감사_{stamp}"
    if not output_dir.is_absolute():
        output_dir = root / output_dir

    findings = classify(root)
    write_reports(root, output_dir, findings)
    print(f"REPORT={output_dir / 'cleanup_report.md'}")
    print(f"CSV={output_dir / 'cleanup_candidates.csv'}")
    print(f"FINDINGS={len(findings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
