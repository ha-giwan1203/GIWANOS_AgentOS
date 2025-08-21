# [ACTIVE] file: scripts/reportkey_dashboard.py
# [ACTIVE] 실행: streamlit run scripts/reportkey_dashboard.py --server.port=8501

from __future__ import annotations

import json
import os
from pathlib import Path

# (선택) .env 읽기
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

# PDF 검색을 위한 PyPDF2
try:
    from PyPDF2 import PdfReader

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

import streamlit as st

# -------- 개선된 검색 기능 --------
TEXT_EXT = {".txt", ".log", ".md", ".json", ".yaml", ".yml", ".py", ".ps1"}


def is_text_file(p: Path) -> bool:
    """텍스트 파일인지 확인"""
    return p.suffix.lower() in TEXT_EXT


def file_contains_key(p: Path, key: str, max_bytes: int = 2_000_000) -> bool:
    """텍스트 파일만 내용 스캔. 바이너리는 스킵. 너무 큰 파일은 앞부분만 읽음."""
    try:
        if is_text_file(p):
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                return key in f.read(max_bytes)
        return False
    except Exception:
        return False


def pdf_contains_key(p: Path, key: str, max_pages: int = 5) -> bool:
    """PDF 파일에서 키 검색 (앞쪽 몇 페이지만 빠르게 스캔)"""
    try:
        if p.suffix.lower() != ".pdf":
            return False
        if not PDF_AVAILABLE:
            return False
        reader = PdfReader(str(p))
        for i, page in enumerate(reader.pages[:max_pages]):
            text = page.extract_text() or ""
            if key in text:
                return True
        return False
    except Exception:
        return False


def match_file(p: Path, key: str) -> bool:
    """파일 매칭: 파일명 또는 내용에서 키 검색"""
    # 1) 파일명 매칭 (PDF도 파일명에 키가 있으므로 바로 잡힘)
    if key in p.name:
        return True
    # 2) PDF 파일은 내용까지 스캔
    if p.suffix.lower() == ".pdf":
        return pdf_contains_key(p, key)
    # 3) 텍스트 파일은 내용까지 스캔
    return file_contains_key(p, key)


def iter_candidate_files(search_dirs: list[Path]) -> list[Path]:
    """검색 대상 파일들 수집"""
    files = []
    for d in search_dirs:
        if not d.exists():
            continue
        for p in d.rglob("*"):
            if p.is_file():
                files.append(p)
    return files


def group_by_kind(paths: list[Path]) -> dict[str, list[Path]]:
    """파일들을 유형별로 분류"""
    buckets = {"pdf": [], "json": [], "md": [], "logs": [], "others": []}
    for p in paths:
        ext = p.suffix.lower()
        if ext == ".pdf":
            buckets["pdf"].append(p)
        elif ext == ".json":
            buckets["json"].append(p)
        elif ext == ".md":
            buckets["md"].append(p)
        elif ext in {".log", ".txt"}:
            buckets["logs"].append(p)
        else:
            buckets["others"].append(p)
    return buckets


# -------- UI --------
st.set_page_config(page_title="VELOS Report Key Search", layout="wide")
st.title("🔎 VELOS REPORT_KEY 대시보드")

# PDF 지원 상태 표시
if not PDF_AVAILABLE:
    st.warning("⚠️ PDF 검색 기능을 사용하려면 `pip install PyPDF2`를 실행하세요.")

report_key = st.text_input("REPORT_KEY 입력", placeholder="예: 20250816_170736_a45102c4")
max_tail = st.slider("로그 표시 줄 수", min_value=50, max_value=500, value=120, step=10)
if st.button("검색 실행", use_container_width=True):
    if not report_key.strip():
        st.warning("REPORT_KEY를 입력하세요.")
        st.stop()

    # 기존: 파일 내용만 grep 하던 부분 → 아래로 교체
    search_dirs = [
        Path(r"C:\giwanos\data\reports\auto"),
        Path(r"C:\giwanos\data\reports\_dispatch"),
        Path(r"C:\giwanos\data\logs"),
        Path(r"C:\giwanos\data\memory"),
        Path(r"C:\giwanos\data\sessions"),
        Path(r"C:\giwanos\data\reflections"),
        Path(r"C:\giwanos\data\snapshots"),
        Path(r"C:\giwanos\data\backups"),
    ]
    # 환경변수로 추가 디렉토리 허용 (세미콜론 구분)
    extra = os.getenv("VELOS_SEARCH_DIRS", "")
    if extra:
        for raw in extra.split(";"):
            p = Path(raw.strip())
            if p.exists():
                search_dirs.append(p)

    candidates = iter_candidate_files(search_dirs)
    hits = [p for p in candidates if match_file(p, report_key)]
    buckets = group_by_kind(hits)

    st.subheader("📁 검색 결과")
    if not hits:
        st.info(
            "검색 결과가 없습니다. 경로가 맞는지 또는 REPORT_KEY가 포함되어 생성되었는지 확인하세요."
        )
        st.code("\n".join(str(p) for p in search_dirs), language="text")
        st.stop()

    # 파일 유형별로 보여주기
    def tail(text: str, n: int) -> str:
        lines = text.splitlines()
        if len(lines) > n:
            return "\n".join(lines[-n:]) + f"\n… (총 {len(lines)}줄 중 마지막 {n}줄만 표시)"
        return "\n".join(lines)

    st.success(f"총 {len(hits)}개 파일에서 REPORT_KEY를 발견했습니다.")

    # PDF/MD/JSON/LOG 섹션
    def section(title: str, items: list[Path]):
        if not items:
            return
        st.markdown(f"### {title}  ({len(items)})")
        for p in sorted(items, key=lambda x: x.name):
            with st.expander(p.name):
                st.write(str(p))
                if p.suffix.lower() == ".json":
                    try:
                        with open(p, "r", encoding="utf-8", errors="ignore") as f:
                            txt = f.read()
                        st.json(json.loads(txt))
                    except Exception:
                        with open(p, "r", encoding="utf-8", errors="ignore") as f:
                            txt = f.read()
                        st.code(tail(txt, max_tail), language="json")
                elif p.suffix.lower() in [".md", ".markdown"]:
                    with open(p, "r", encoding="utf-8", errors="ignore") as f:
                        txt = f.read()
                    st.code(tail(txt, max_tail), language="markdown")
                elif p.suffix.lower() in [".log", ".txt"]:
                    with open(p, "r", encoding="utf-8", errors="ignore") as f:
                        txt = f.read()
                    st.code(tail(txt, max_tail), language="log")
                elif p.suffix.lower() == ".pdf":
                    if PDF_AVAILABLE:
                        try:
                            reader = PdfReader(str(p))
                            st.write(f"PDF 파일 (총 {len(reader.pages)}페이지)")
                            # 앞쪽 3페이지 텍스트 표시
                            for i, page in enumerate(reader.pages[:3]):
                                text = page.extract_text() or ""
                                if text.strip():
                                    st.code(
                                        f"--- 페이지 {i+1} ---\n{tail(text, 50)}", language="text"
                                    )
                        except Exception as e:
                            st.write(f"PDF 파일입니다. 읽기 오류: {e}")
                    else:
                        st.write("PDF 파일입니다. 경로를 클릭해 열어보세요.")
                else:
                    if is_text_file(p):
                        with open(p, "r", encoding="utf-8", errors="ignore") as f:
                            txt = f.read()
                        st.code(tail(txt, max_tail))
                    else:
                        st.write("바이너리 파일입니다.")

    section("📄 PDF / 리포트", buckets["pdf"])
    section("📝 Markdown", buckets["md"])
    section("🧾 JSON", buckets["json"])
    section("📜 로그(TXT/LOG)", buckets["logs"])
    section("기타", buckets["others"])

# 사이드바: 검색 예시/경로
with st.sidebar:
    st.markdown("### 📂 검색 경로")
    search_dirs = [
        Path(r"C:\giwanos\data\reports\auto"),
        Path(r"C:\giwanos\data\reports\_dispatch"),
        Path(r"C:\giwanos\data\logs"),
        Path(r"C:\giwanos\data\memory"),
        Path(r"C:\giwanos\data\sessions"),
        Path(r"C:\giwanos\data\reflections"),
        Path(r"C:\giwanos\data\snapshots"),
        Path(r"C:\giwanos\data\backups"),
    ]
    st.code("\n".join(str(p) for p in search_dirs if p.exists()), language="text")
    st.markdown("— 경로를 추가하려면 환경변수 `VELOS_SEARCH_DIRS`를 세미콜론(;)으로 추가하세요.")

    if PDF_AVAILABLE:
        st.success("✅ PDF 검색 기능 활성화")
    else:
        st.warning("⚠️ PDF 검색 기능 비활성화")
