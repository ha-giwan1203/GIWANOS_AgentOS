#!config.PROJECT_HOMEbin/env python
# scripts/verify_structure.py
from modules.core import config
"""
프로젝트 루트 이하의 디렉터리/파일 구조를 사양(spec)과 비교해
 ▫︎ 누락(Missing)
 ▫︎ 타입 불일치(Type‑mismatch: dir↔file)
 ▫︎ 여분(Extras: spec 에 없는데 실제 존재)
을 검증·보고한다.

기본 사양은 하단의 EXPECTED_DIRS / EXPECTED_FILES 로 정의되며,
--override 옵션으로 YAML 파일을 주면 해당 내용이 기본 사양을 덮어쓴다.
YAML 형태 예)
    fonts/NanumGothic-Regular.ttf: file
    venv: ignore        # 완전히 무시
값 의미
    dir   : 반드시 폴더여야 함
    file  : 반드시 파일이어야 함
    ignore: 검사 대상에서 제외
    any   : 존재만 하면 OK (타입 무관)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import yaml
except ImportError:  # PyYAML 이 없으면 간략 파서 사용
    import json as yaml  # type: ignore

# ──────────────────────────────────────────────────────────────
# 1) 기본 사양 ------------------------------------------------------------------
EXPECTED_DIRS = [
    "fonts",
    "data",
    "data/snapshots",
    "vector_cache",
    "modules",
    "modules/core",
    "scripts",
]
EXPECTED_FILES = [
    "modules/core/path_utils.py",
    "spec_overrides.yaml",  # 사양 재정의 파일 자체도 버전 관리 권장
]

DEFAULT_SPEC: Dict[str, str] = {p: "dir" for p in EXPECTED_DIRS}
DEFAULT_SPEC.update({p: "file" for p in EXPECTED_FILES})

# ──────────────────────────────────────────────────────────────
# 2) 헬퍼 함수 ---------------------------------------------------------------


def build_spec(case_insensitive: bool, override_path: Path | None) -> Dict[str, str]:
    """
    기본 사양 + (선택)YAML 덮어쓰기 → 최종 사양 dict(str→str)
    """
    spec: Dict[str, str] = DEFAULT_SPEC.copy()
    if override_path:
        try:
            with override_path.open("r", encoding="utf-8") as fp:
                overrides = yaml.safe_load(fp) or {}
            if not isinstance(overrides, dict):
                raise TypeError("override YAML root must be a mapping")
            overrides = {str(k): str(v) for k, v in overrides.items()}
            spec.update(overrides)
        except Exception as exc:
            sys.exit(f"[verify_structure] YAML 읽기 오류: {exc}")

    # 케이스 무시 옵션
    if case_insensitive:
        spec = {p.lower(): v for p, v in spec.items()}
    return spec


def scan(
    root: Path,
    spec: Dict[str, str],
    case_insensitive: bool,
    show_extras: bool,
) -> Tuple[List[str], List[str], List[str]]:
    """
    사양과 실제 파일시스템 비교 → (missing, mismatched, extras) 리스트 반환
    """
    missing, mismatch, extras = [], [], []

    # ① 존재/타입 확인
    for rel_path, expected_type in spec.items():
        if expected_type == "ignore":  # 완전 무시
            continue

        rel = Path(rel_path)
        abs_path = root / rel
        if case_insensitive:
            # 윈도·mac 처럼 대소문자 무시 시, 실제 존재 여부 수동 확인
            matches = list(abs_path.parent.glob(rel.name))
            abs_path = matches[0] if matches else abs_path

        if not abs_path.exists():
            missing.append(rel_path)
            continue

        # 타입 체크
        if expected_type == "dir" and not abs_path.is_dir():
            mismatch.append(f"{rel_path}  (expected DIR, found FILE)")
        elif expected_type == "file" and not abs_path.is_file():
            mismatch.append(f"{rel_path}  (expected FILE, found DIR)")

    # ② 여분 탐색 (spec 에 없는데 실제 존재)
    if show_extras:
        spec_paths = {p.lower() if case_insensitive else p for p in spec.keys()}
        for path in root.rglob("*"):
            if path.is_symlink():
                continue
            rel = path.relative_to(root).as_posix()
            key = rel.lower() if case_insensitive else rel
            if key in spec_paths:
                continue
            extras.append(rel)

    return missing, mismatch, extras


def report(
    missing: List[str],
    mismatch: List[str],
    extras: List[str],
    show_extras: bool,
) -> None:
    """콘솔 출력"""
    if not (missing or mismatch or (show_extras and extras)):
        print("✅  구조가 사양과 일치합니다.")
        return

    if missing:
        print("\n❌  누락(Missing)")
        for p in missing:
            print(f"  - {p}")

    if mismatch:
        print("\n⚠️  타입 불일치(Mismatch)")
        for p in mismatch:
            print(f"  - {p}")

    if show_extras and extras:
        print("\nℹ️  여분(Extras)")
        for p in extras:
            print(f"  - {p}")


# ──────────────────────────────────────────────────────────────
# 3) CLI 엔트리 --------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="프로젝트 구조 검증 스크립트")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="검사 대상 프로젝트 루트 (기본: repo 최상위)",
    )
    parser.add_argument(
        "--override",
        type=Path,
        metavar="YAML",
        help="사양을 덮어쓸 YAML 파일 경로",
    )
    parser.add_argument(
        "--case-insensitive",
        action="store_true",
        help="경로 대소문자 무시(Windows/macOS 용)",
    )
    parser.add_argument(
        "--show-extras",
        action="store_true",
        help="사양에 정의되지 않은 여분 파일/폴더도 표시",
    )
    args = parser.parse_args()

    spec = build_spec(args.case_insensitive, args.override)

    missing, mismatch, extras = scan(
        args.root, spec, args.case_insensitive, args.show_extras
    )

    report(missing, mismatch, extras, args.show_extras)

    # CI 용 종료코드: 문제 있으면 1
    if missing or mismatch:
        sys.exit(1)


if __name__ == "__main__":
    main()



