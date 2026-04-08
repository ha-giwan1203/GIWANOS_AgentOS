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

VALID_GRADES = {"A", "B", "C"}

# 스킬 3등급 분류 기준표
SKILL_GRADE_MAP = {
    "adversarial-review": "C",
    "assembly-cost-settlement": "B",
    "cdp-wrapper": "A",
    "chomul-module-partno": "A",
    "cost-rate-management": "B",
    "equipment-utilization": "C",
    "flow-chat-analysis": "C",
    "hr-attendance": "C",
    "line-batch-mainsub": "A",
    "line-batch-management": "A",
    "line-batch-outer-main": "A",
    "line-mapping-validator": "B",
    "line-stoppage": "C",
    "night-scan-compare": "B",
    "partno-management": "C",
    "pptx-generator": "B",
    "process-improvement": "C",
    "procurement-delivery": "C",
    "production-report": "B",
    "production-result-upload": "A",
    "quality-assurance": "C",
    "quality-defect-report": "C",
    "skill-creator-merged": "B",
    "sp3-production-plan": "B",
    "supanova-deploy": "A",
    "youtube-analysis": "C",
    "zdm-daily-inspection": "A",
}

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


PLACEHOLDER_PATTERNS = re.compile(r"\{[^}]*\}", re.UNICODE)


def has_unresolved_placeholder(section_text: str) -> bool:
    """템플릿 플레이스홀더({실패로 간주할 상황} 등) 미치환 탐지."""
    return bool(PLACEHOLDER_PATTERNS.search(section_text))


def is_meaningful(section_text: str) -> bool:
    cleaned = re.sub(r"[\s\-\*\d\.\{\}]", "", section_text)
    return len(cleaned) > 5


def extract_grade(text: str) -> str | None:
    """YAML frontmatter에서 grade 필드 추출."""
    m = re.search(r"^grade:\s*([ABCabc])\s*$", text, re.MULTILINE)
    return m.group(1).upper() if m else None


def skill_dir_name(file_path: Path) -> str:
    """SKILL.md 경로에서 스킬 디렉토리명 추출."""
    return file_path.parent.name


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

    grade_warnings = []

    for file_path in files:
        text = file_path.read_text(encoding="utf-8")
        missing = []
        empty = []
        placeholder = []

        for heading in REQUIRED_HEADINGS:
            if heading not in text:
                missing.append(heading)
                continue
            section_text = extract_section(text, heading)
            if not is_meaningful(section_text):
                empty.append(heading)
            elif has_unresolved_placeholder(section_text):
                placeholder.append(heading)

        # grade 검증
        dir_name = skill_dir_name(file_path)
        grade_in_file = extract_grade(text)
        expected_grade = SKILL_GRADE_MAP.get(dir_name)
        if grade_in_file is None:
            grade_warnings.append(f"{dir_name}: grade 필드 없음 (기대값: {expected_grade or '?'})")
        elif expected_grade and grade_in_file != expected_grade:
            grade_warnings.append(f"{dir_name}: grade={grade_in_file} ≠ 기대값 {expected_grade}")

        if missing or empty or placeholder:
            failures.append({
                "file": str(file_path),
                "grade": grade_in_file or expected_grade or "?",
                "missing": missing,
                "empty": empty,
                "placeholder": placeholder,
            })
        else:
            passes.append({"file": str(file_path), "grade": grade_in_file or expected_grade or "?"})

    # report 생성
    report_lines = []
    report_lines.append("# Skill Contract Gap Report")
    report_lines.append("")
    report_lines.append(f"- 검사 대상: {len(files)}개")
    report_lines.append(f"- PASS: {len(passes)}개 (자동화 완성 스킬)")
    report_lines.append(f"- FAIL: {len(failures)}개 (미자동화 스킬 포함, 의도적 제외 대상 다수)")
    report_lines.append("")

    # grade 분류 요약
    report_lines.append("## 스킬 3등급 분류")
    report_lines.append("")
    report_lines.append("| 등급 | 정의 | 수량 |")
    report_lines.append("|------|------|------|")
    grade_counts = {"A": 0, "B": 0, "C": 0}
    for g in SKILL_GRADE_MAP.values():
        grade_counts[g] += 1
    report_lines.append(f"| A (실행형) | 브라우저/ERP/MES/API 직접 조작 | {grade_counts['A']}개 |")
    report_lines.append(f"| B (파일수정형) | 엑셀/코드/문서 생성·수정 | {grade_counts['B']}개 |")
    report_lines.append(f"| C (분석형) | 읽기 전용 분석·보고 | {grade_counts['C']}개 |")
    report_lines.append("")

    if grade_warnings:
        report_lines.append("## Grade 경고")
        report_lines.append("")
        for w in grade_warnings:
            report_lines.append(f"- WARN: {w}")
        report_lines.append("")

    if failures:
        report_lines.append("## FAIL 목록")
        report_lines.append("")
        for item in failures:
            grade_label = item.get("grade", "?")
            report_lines.append(f"### [{grade_label}] {item['file']}")
            if item["missing"]:
                report_lines.append(f"- 누락: {', '.join(item['missing'])}")
            if item["empty"]:
                report_lines.append(f"- 비어있음: {', '.join(item['empty'])}")
            if item.get("placeholder"):
                report_lines.append(f"- 플레이스홀더 미치환: {', '.join(item['placeholder'])}")
            report_lines.append("")

    if passes:
        report_lines.append("## PASS 목록")
        report_lines.append("")
        for p in passes:
            if isinstance(p, dict):
                report_lines.append(f"- [{p.get('grade', '?')}] {p['file']}")
            else:
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
