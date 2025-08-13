# VELOS 운영 철학 선언문
# - 파일명 절대 변경 금지 · 모든 수정 후 자가 검증 필수 · 실행 결과 직접 테스트
# - 결정·기억·보고의 모든 흐름은 구조적 사고와 기록을 기반으로 유지해야 한다.

from __future__ import annotations

import glob
import py_compile
import sys
from pathlib import Path

from modules.report_paths import ROOT, P
SNAPSHOT_DIR = ROOT / r"data\snapshots"

REQUIRED_DIRS = [
    ROOT / "configs",
    ROOT / r"data\logs",
    ROOT / r"data\reports",
    ROOT / r"data\memory",
    SNAPSHOT_DIR,
    ROOT / "docs",
    ROOT / "interface",
    ROOT / "modules",
    ROOT / "scripts",
    ROOT / "tools",
    ROOT / "vector_cache",
]


def fail(msg: str, code: int = 2):
    print(f"[FAIL] {msg}")
    sys.exit(code)


def ok(msg: str):
    print(f"[OK] {msg}")


def check_dirs():
    for d in REQUIRED_DIRS:
        if not d.exists():
            fail(f"필수 폴더 누락: {d}")
    if str(SNAPSHOT_DIR).lower() != str(P("data/snapshots")).lower():
        fail("스냅샷 경로가 고정값과 불일치")
    ok("필수 폴더 및 스냅샷 경로 확인")


def compile_all():
    targets = []
    for base in ["scripts", "modules", "tools", "interface"]:
        targets += glob.glob(str(ROOT / base / "**" / "*.py"), recursive=True)
    errors = []
    for f in targets:
        try:
            py_compile.compile(f, doraise=True)
        except Exception as e:
            errors.append((f, repr(e)))
    if errors:
        print("[FAIL] 문법 오류 파일 목록:")
        for f, e in errors:
            print(" -", f, "=>", e)
        sys.exit(3)
    ok(f"문법 검증 통과: {len(targets)} files")


def main():
    if not ROOT.exists():
        fail(""{0} 루트 없음" -f ROOT")
    check_dirs()
    compile_all()
    ok("프리플라이트 통과")


if __name__ == "__main__":
    main()




