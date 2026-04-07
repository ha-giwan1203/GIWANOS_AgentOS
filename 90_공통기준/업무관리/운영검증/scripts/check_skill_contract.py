#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SKILL.md 실패계약 린터
- 필수 4섹션 (실패 조건 / 중단 기준 / 검증 항목 / 되돌리기 방법) 존재 여부 검사
- 섹션이 비어있으면 경고
- 결과를 gap report로 출력
"""
import argparse
import re
import sys
from pathlib import Path

REQUIRED_HEADINGS = [
    "## 실패 조건",
    "## 중단 기준",
    "## 검증 항목",
    "## 되돌리기 방법",
]

IGNORE_NAMES = {"SKILL_TEMPLATE.md", "README.md", "INDEX.md"}
IGNORE_DIRS = {"_lint", "_audit", "_examples", "__pycache__", "_archive"}


def should_ignore(path: Path) -> bool:
    return any(part in IGNORE_DIRS for part in path.parts)


def find_skill_files(root: Path) -> list[Path]:
    return [
        p for p in root.rglob("SKILL.md")
        if p.is_file() and not should_ignore(p) and p.name not in IGNORE_NAMES
    ]


def extract_section(text: str, heading: str) -> str:
    pattern = rf"{re.escape(heading)}\s*(.*?)(?=\n## |\Z)"
    m = re.search(pattern, text, flags=re.DOTALL)
    return m.group(1).strip() if m else ""


def is_meaningful(section_text: str) -> bool:
    cleaned = re.sub(r"[\s\-\*\d\.\{\}]", "", section_text)
    return len(cleaned) > 5


def main():
    parser = argparse.ArgumentParser(description="SKILL.md 실패계약 린터")
    parser.add_argument(
        "root",
        nargs="?",
        default="90_공통기준/스킬",
        help="검사 대상 루트 폴더",
    )
    parser.add_argument("--write-report", default=None, help="gap report 출력 경로")
    args = parser.parse_args()

    root = Path(args.root)
    files = find_skill_files(root)
    failures = []
    passes = []

    for file_path in files:
        text = file_path.read_text(encoding="utf-8")
        missing = []
        empty = []

        for heading in REQUIRED_HEADINGS:
            if heading not in text:
                missing.append(heading)
                continue
            section_text = extract_section(text, heading)
            if not is_meaningful(section_text):
                empty.append(heading)

        if missing or empty:
            failures.append({
                "file": str(file_path),
                "missing": missing,
                "empty": empty,
            })
        else:
            passes.append(str(file_path))

    # report 생성
    report_lines = []
    report_lines.append("# Skill Contract Gap Report")
    report_lines.append("")
    report_lines.append(f"- 검사 대상: {len(files)}개")
    report_lines.append(f"- PASS: {len(passes)}개")
    report_lines.append(f"- FAIL: {len(failures)}개")
    report_lines.append("")

    if failures:
        report_lines.append("## FAIL 목록")
        report_lines.append("")
        for item in failures:
            report_lines.append(f"### {item['file']}")
            if item["missing"]:
                report_lines.append(f"- 누락: {', '.join(item['missing'])}")
            if item["empty"]:
                report_lines.append(f"- 비어있음: {', '.join(item['empty'])}")
            report_lines.append("")

    if passes:
        report_lines.append("## PASS 목록")
        report_lines.append("")
        for p in passes:
            report_lines.append(f"- {p}")
        report_lines.append("")

    report_text = "\n".join(report_lines)

    if args.write_report:
        out_path = Path(args.write_report)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report_text, encoding="utf-8")
        print(f"Report → {out_path}")

    print(report_text)

    if failures:
        sys.exit(1)
    else:
        print("PASS: 모든 스킬에 실패계약 4섹션 존재")
        sys.exit(0)


if __name__ == "__main__":
    main()
