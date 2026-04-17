"""
NotebookLM 업로드용 라인배치 도메인 통합 소스 생성기

실행: python 10_라인배치/build_notebooklm_source.py
출력: 10_라인배치/notebooklm_source_라인배치_v1.txt

settlement 파일럿 패턴 (notebooklm_source_조립비정산_v1.txt) 참고.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "10_라인배치" / "notebooklm_source_라인배치_v1.txt"

# 병합 순서: 운영규칙 → 진행상태 → 도메인개요 → 라인매핑기준 → 4개 스킬
DOCS = [
    ("10_라인배치/CLAUDE.md", "운영 규칙"),
    ("10_라인배치/STATUS.md", "진행 상태"),
    ("10_라인배치/README.md", "도메인 개요"),
    ("10_라인배치/라인배치_스킬문서_v9.md", "라인 매핑 기준 v9"),
    ("90_공통기준/스킬/line-batch-management/SKILL.md", "스킬: line-batch-management (OUTER 메인 자동화)"),
    ("90_공통기준/스킬/line-batch-outer-main/SKILL.md", "스킬: line-batch-outer-main (OUTER/MAIN 통합)"),
    ("90_공통기준/스킬/line-batch-mainsub/SKILL.md", "스킬: line-batch-mainsub (메인서브 자동화)"),
    ("90_공통기준/스킬/line-mapping-validator/SKILL.md", "스킬: line-mapping-validator (정합성 검증)"),
]


def build() -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    total = len(DOCS)
    chunks: list[str] = []

    chunks.append("# NotebookLM 업로드용 통합 소스 — 라인배치 도메인\n")
    chunks.append(f"\n생성일: {today}\n")
    chunks.append(f"원본: 업무리스트 저장소 10_라인배치/ + 90_공통기준/스킬/ 하위 {total}개 문서\n")
    chunks.append("목적: NotebookLM 단일 소스로 라인 매핑·ERP 셀렉터·재개 규칙 전체 검색 가능하게 함\n\n")

    for idx, (rel, title) in enumerate(DOCS, start=1):
        src = REPO / rel
        if not src.exists():
            raise FileNotFoundError(f"누락: {rel}")
        body = src.read_text(encoding="utf-8")
        chunks.append("========================================\n")
        chunks.append(f"# [{idx}/{total}] {title}\n")
        chunks.append(f"원본경로: {rel}\n")
        chunks.append("========================================\n\n")
        chunks.append(body)
        if not body.endswith("\n"):
            chunks.append("\n")
        chunks.append("\n")

    OUT.write_text("".join(chunks), encoding="utf-8")
    lines = OUT.read_text(encoding="utf-8").count("\n")
    size_kb = OUT.stat().st_size / 1024
    print(f"생성: {OUT.relative_to(REPO)}")
    print(f"라인: {lines:,} / 크기: {size_kb:.1f} KB / 문서: {total}개")


if __name__ == "__main__":
    build()
