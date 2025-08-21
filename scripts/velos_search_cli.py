# [ACTIVE] VELOS 검색 CLI - 명령줄 기반 검색 도구
# -*- coding: utf-8 -*-
"""
VELOS REPORT_KEY 명령줄 검색 도구
- REPORT_KEY로 모든 관련 파일 검색
- 간단한 명령줄 인터페이스
"""

import glob
import os
import sys
from datetime import datetime
from pathlib import Path


def search_in_file(file_path, search_key):
    """파일에서 REPORT_KEY 검색"""
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            content = f.read()
            if search_key in content:
                return True
    except:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if search_key in content:
                    return True
        except:
            pass
    return False


def search_report_key(report_key):
    """REPORT_KEY로 모든 관련 파일 검색"""
    results = {
        "logs": [],
        "reports": [],
        "reflections": [],
        "memory": [],
        "sessions": [],
        "snapshots": [],
    }

    base_path = Path("/home/user/webapp")

    # 로그 파일 검색
    for log_file in glob.glob(str(base_path / "data/logs/*.json")):
        if search_in_file(log_file, report_key):
            results["logs"].append(log_file)

    # 보고서 파일 검색
    for report_file in glob.glob(str(base_path / "data/reports/**/*"), recursive=True):
        if os.path.isfile(report_file) and report_key in report_file:
            results["reports"].append(report_file)

    # 회고 파일 검색
    for ref_file in glob.glob(str(base_path / "data/reflections/*.json")):
        if search_in_file(ref_file, report_key):
            results["reflections"].append(ref_file)

    # 메모리 파일 검색
    for mem_file in glob.glob(str(base_path / "data/memory/*.json")):
        if search_in_file(mem_file, report_key):
            results["memory"].append(mem_file)

    # 세션 파일 검색
    for session_file in glob.glob(str(base_path / "data/sessions/*.json")):
        if search_in_file(session_file, report_key):
            results["sessions"].append(session_file)

    # 스냅샷 파일 검색
    for snap_file in glob.glob(str(base_path / "data/snapshots/**/*"), recursive=True):
        if os.path.isfile(snap_file) and report_key in snap_file:
            results["snapshots"].append(snap_file)

    return results


def format_file_size(size_bytes):
    """파일 크기 포맷팅"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def main():
    """메인 함수"""
    if len(sys.argv) != 2:
        print("사용법: python velos_search_cli.py <REPORT_KEY>")
        print("예시: python velos_search_cli.py 20250816_170736_a45102c4")
        sys.exit(1)

    report_key = sys.argv[1]

    if len(report_key) < 10:
        print("❌ REPORT_KEY가 너무 짧습니다.")
        print("올바른 형식: YYYYMMDD_HHMMSS_xxxxxxxx")
        sys.exit(1)

    print(f"🔍 '{report_key}' 검색 중...")
    print("=" * 50)

    results = search_report_key(report_key)

    total_files = sum(len(files) for files in results.values())
    print(f"📊 총 {total_files}개의 관련 파일을 찾았습니다.\n")

    # 각 카테고리별 결과 출력
    for category, files in results.items():
        if files:
            print(f"📂 {category.upper()} ({len(files)}개):")
            for file_path in files:
                try:
                    size = format_file_size(os.path.getsize(file_path))
                    modified = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    file_name = os.path.basename(file_path)
                    print(f"   📄 {file_name}")
                    print(f"      📏 크기: {size}")
                    print(f"      🕒 수정: {modified}")
                    print(f"      📍 경로: {file_path}")
                    print()
                except:
                    print(f"   📄 {file_path}")
                    print()
        else:
            print(f"📂 {category.upper()}: 없음")

    # Notion DB 정보
    notion_db_id = os.getenv("NOTION_DATABASE_ID")
    if notion_db_id:
        print("📋 NOTION DB:")
        print(f"   Database ID: {notion_db_id}")
        print(
            f"   검색 URL: https://notion.so/{notion_db_id.replace('-', '')}?v=search&q={report_key}"
        )
        print()

    print("🔍 검색 완료!")


if __name__ == "__main__":
    main()
