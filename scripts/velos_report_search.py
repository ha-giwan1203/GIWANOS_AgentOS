# -*- coding: utf-8 -*-
"""
VELOS REPORT_KEY 검색 앱
- REPORT_KEY로 모든 관련 파일 검색
- 로그, 보고서, 회고, 메모리 파일 탐색
- Streamlit 기반 웹 인터페이스
"""

import streamlit as st
import os
import json
import glob
import re
from pathlib import Path
from datetime import datetime


def search_in_file(file_path, search_key):
    """파일에서 REPORT_KEY 검색"""
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            content = f.read()
            if search_key in content:
                return True, content
    except Exception as e:
        try:
            # UTF-8로 재시도
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if search_key in content:
                    return True, content
        except:
            pass
    return False, ""


def search_report_key(report_key: str):
    """REPORT_KEY로 모든 관련 파일 검색"""
    results = {
        "logs": [],
        "reports": [],
        "reflections": [],
        "memory": [],
        "sessions": [],
        "snapshots": [],
        "notion_entries": []
    }

    # 검색 경로 설정
    base_path = Path("C:/giwanos")

    # 1. 로그 파일 검색
    log_patterns = [
        "data/logs/*.json",
        "data/logs/*.log",
        "data/logs/*.txt"
    ]

    for pattern in log_patterns:
        for log_file in glob.glob(str(base_path / pattern)):
            found, content = search_in_file(log_file, report_key)
            if found:
                results["logs"].append({
                    "file": log_file,
                    "size": os.path.getsize(log_file),
                    "modified": datetime.fromtimestamp(os.path.getmtime(log_file)).isoformat()
                })

    # 2. 보고서 파일 검색
    report_patterns = [
        "data/reports/*.pdf",
        "data/reports/*.md",
        "data/reports/*.json",
        "data/reports/auto/*.pdf",
        "data/reports/auto/*.md"
    ]

    for pattern in report_patterns:
        for report_file in glob.glob(str(base_path / pattern)):
            if report_key in report_file:
                results["reports"].append({
                    "file": report_file,
                    "size": os.path.getsize(report_file),
                    "modified": datetime.fromtimestamp(os.path.getmtime(report_file)).isoformat()
                })

    # 3. 회고 파일 검색
    reflection_patterns = [
        "data/reflections/*.json"
    ]

    for pattern in reflection_patterns:
        for ref_file in glob.glob(str(base_path / pattern)):
            found, content = search_in_file(ref_file, report_key)
            if found:
                results["reflections"].append({
                    "file": ref_file,
                    "size": os.path.getsize(ref_file),
                    "modified": datetime.fromtimestamp(os.path.getmtime(ref_file)).isoformat()
                })

    # 4. 메모리 파일 검색
    memory_patterns = [
        "data/memory/*.json",
        "data/memory/*.jsonl",
        "data/memory/*.db"
    ]

    for pattern in memory_patterns:
        for mem_file in glob.glob(str(base_path / pattern)):
            found, content = search_in_file(mem_file, report_key)
            if found:
                results["memory"].append({
                    "file": mem_file,
                    "size": os.path.getsize(mem_file),
                    "modified": datetime.fromtimestamp(os.path.getmtime(mem_file)).isoformat()
                })

    # 5. 세션 파일 검색
    session_patterns = [
        "data/sessions/*.json"
    ]

    for pattern in session_patterns:
        for session_file in glob.glob(str(base_path / pattern)):
            found, content = search_in_file(session_file, report_key)
            if found:
                results["sessions"].append({
                    "file": session_file,
                    "size": os.path.getsize(session_file),
                    "modified": datetime.fromtimestamp(os.path.getmtime(session_file)).isoformat()
                })

    # 6. 스냅샷 파일 검색
    snapshot_patterns = [
        "data/snapshots/*.json",
        "data/snapshots/*.zip"
    ]

    for pattern in snapshot_patterns:
        for snap_file in glob.glob(str(base_path / pattern)):
            if report_key in snap_file:
                results["snapshots"].append({
                    "file": snap_file,
                    "size": os.path.getsize(snap_file),
                    "modified": datetime.fromtimestamp(os.path.getmtime(snap_file)).isoformat()
                })

    # 7. Notion DB 검색 (환경변수 확인)
    notion_db_id = os.getenv("NOTION_DATABASE_ID")
    if notion_db_id:
        results["notion_entries"].append({
            "database_id": notion_db_id,
            "search_url": f"https://notion.so/{notion_db_id.replace('-', '')}?v=search&q={report_key}",
            "note": "Notion DB에서 직접 검색 필요"
        })

    return results


def format_file_size(size_bytes):
    """파일 크기 포맷팅"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def display_search_results(results, report_key):
    """검색 결과 표시"""
    st.subheader(f"🔍 '{report_key}' 검색 결과")

    total_files = sum(len(files) for files in results.values())
    st.info(f"총 {total_files}개의 관련 파일을 찾았습니다.")

    # 각 카테고리별 결과 표시
    for category, files in results.items():
        if files:
            st.write(f"### {category.replace('_', ' ').title()} ({len(files)}개)")

            if category == "notion_entries":
                for entry in files:
                    st.write(f"- **Database ID**: {entry['database_id']}")
                    st.write(f"- **검색 링크**: [Notion에서 검색]({entry['search_url']})")
                    st.write(f"- **참고**: {entry['note']}")
            else:
                for file_info in files:
                    file_path = file_info["file"]
                    file_size = format_file_size(file_info["size"])
                    modified_time = file_info["modified"]

                    # 파일명만 추출
                    file_name = os.path.basename(file_path)

                    col1, col2, col3 = st.columns([3, 1, 2])
                    with col1:
                        st.write(f"📄 **{file_name}**")
                    with col2:
                        st.write(f"📏 {file_size}")
                    with col3:
                        st.write(f"🕒 {modified_time[:19]}")

                    # 전체 경로 표시 (접을 수 있게)
                    with st.expander("전체 경로"):
                        st.code(file_path)

            st.divider()


def main():
    """메인 Streamlit 앱"""
    st.set_page_config(
        page_title="VELOS Report Key Search",
        page_icon="🔍",
        layout="wide"
    )

    st.title("🔍 VELOS Report Key Search")
    st.markdown("REPORT_KEY로 VELOS 시스템의 모든 관련 파일을 검색합니다.")

    # 사이드바
    with st.sidebar:
        st.header("🔧 검색 옵션")

        # REPORT_KEY 입력
        report_key = st.text_input(
            "REPORT_KEY 입력",
            placeholder="예: 20250816_170736_a45102c4",
            help="검색할 REPORT_KEY를 입력하세요"
        )

        # 검색 버튼
        search_button = st.button("🔍 검색", type="primary")

        # 예시 REPORT_KEY
        st.markdown("### 📋 예시 REPORT_KEY")
        st.code("20250816_170736_a45102c4")
        st.code("20250816_144400_abcd1234")

        # 검색 범위 정보
        st.markdown("### 📂 검색 범위")
        st.markdown("""
        - 📄 **로그**: API 비용, 시스템 상태
        - 📊 **보고서**: PDF, Markdown, JSON
        - 🤔 **회고**: reflection_*.json
        - 🧠 **메모리**: learning_memory, dialog_memory
        - 📝 **세션**: session_*.json
        - 📸 **스냅샷**: backup_*.json, *.zip
        - 📋 **Notion**: DB 검색 링크
        """)

    # 메인 영역
    if search_button and report_key:
        if len(report_key) < 10:
            st.error("❌ REPORT_KEY가 너무 짧습니다. 올바른 형식을 확인해주세요.")
            st.info("올바른 형식: YYYYMMDD_HHMMSS_xxxxxxxx")
        else:
            with st.spinner("🔍 파일을 검색하고 있습니다..."):
                results = search_report_key(report_key)

            display_search_results(results, report_key)

            # 결과 요약
            st.subheader("📊 검색 결과 요약")
            summary_data = {
                "카테고리": list(results.keys()),
                "파일 수": [len(files) for files in results.values()]
            }
            st.bar_chart(summary_data)

    elif search_button and not report_key:
        st.warning("⚠️ REPORT_KEY를 입력해주세요.")

    # 사용법 안내
    else:
        st.markdown("""
        ### 🚀 사용법

        1. **REPORT_KEY 입력**: 검색할 REPORT_KEY를 입력하세요
        2. **검색 실행**: 🔍 검색 버튼을 클릭하세요
        3. **결과 확인**: 관련된 모든 파일을 확인하세요

        ### 📋 REPORT_KEY 형식

        REPORT_KEY는 다음과 같은 형식입니다:
        ```
        YYYYMMDD_HHMMSS_xxxxxxxx
        ```

        - **YYYYMMDD**: 날짜 (예: 20250816)
        - **HHMMSS**: 시간 (예: 170736)
        - **xxxxxxxx**: 고유 ID (8자리)

        ### 🔍 검색 예시

        - `20250816_170736_a45102c4`
        - `20250816_144400_abcd1234`
        - `20250815_090000_12345678`

        ### 📂 검색되는 파일들

        - **로그 파일**: API 비용, 시스템 상태 로그
        - **보고서**: PDF, Markdown, JSON 보고서
        - **회고**: reflection_*.json 파일들
        - **메모리**: learning_memory, dialog_memory 등
        - **세션**: session_*.json 파일들
        - **스냅샷**: 백업 및 스냅샷 파일들
        - **Notion**: DB 검색 링크 제공
        """)

    # 푸터
    st.markdown("---")
    st.markdown("*VELOS Report Key Search - VELOS 시스템의 모든 관련 파일을 쉽게 찾아보세요*")


if __name__ == "__main__":
    main()
