# -*- coding: utf-8 -*-
"""
VELOS Notion 통합 테스트 스크립트
- DB 생성 + Page 생성 연계 테스트
- 실제 보고서 파일 사용
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# 환경변수 로딩
try:
    from env_loader import load_env
    load_env()
except ImportError:
    print("⚠️  env_loader 모듈을 찾을 수 없습니다", file=sys.stderr)
    sys.exit(1)


def run_script(script_name, env_vars=None):
    """Python 스크립트 실행"""
    cmd = [sys.executable, f"scripts/{script_name}"]

    # 환경변수 설정
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )

        if result.returncode == 0:
            # JSON 출력 파싱
            try:
                output_lines = result.stdout.strip().split('\n')
                json_line = output_lines[-1]  # 마지막 줄이 JSON
                return json.loads(json_line)
            except (json.JSONDecodeError, IndexError):
                return {"ok": True, "output": result.stdout}
        else:
            return {
                "ok": False,
                "error": result.stderr,
                "returncode": result.returncode
            }

    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "타임아웃"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def find_latest_reports():
    """최신 보고서 파일 찾기"""
    auto_dir = Path(r"C:\giwanos\data\reports\auto")

    try:
        latest_pdf = max(auto_dir.glob("velos_auto_report_*_ko.pdf"))
        latest_md = max(auto_dir.glob("velos_auto_report_*.md"))
        return str(latest_pdf), str(latest_md)
    except ValueError:
        print("❌ 보고서 파일을 찾을 수 없습니다")
        return None, None


def main():
    """메인 테스트 함수"""
    print("🧪 VELOS Notion 통합 테스트")
    print("=" * 50)

    # 최신 보고서 파일 찾기
    pdf_path, md_path = find_latest_reports()
    if not pdf_path or not md_path:
        return 1

    print(f"📄 테스트 파일:")
    print(f"   PDF: {Path(pdf_path).name}")
    print(f"   MD:  {Path(md_path).name}")

    # 1단계: DB 생성 테스트
    print("\n🔹 1단계: Notion DB 생성 테스트")
    print("-" * 30)

    db_env = {
        "VELOS_TITLE": "VELOS 통합 테스트 - DB",
        "VELOS_STATUS": "진행 중",
        "VELOS_TAGS": "테스트,통합,자동화"
    }

    db_result = run_script("notion_db_create.py", db_env)

    if db_result.get("ok"):
        print("✅ DB 생성 성공!")
        print(f"   페이지 ID: {db_result.get('page_id')}")
        db_page_id = db_result.get("page_id")
    else:
        print("❌ DB 생성 실패:")
        print(f"   오류: {db_result.get('error')}")
        return 1

    # 2단계: Page 생성 테스트 (DB 하위)
    print("\n🔹 2단계: Notion Page 생성 테스트 (DB 하위)")
    print("-" * 40)

    page_env = {
        "VELOS_TITLE": "VELOS 통합 테스트 - Page",
        "VELOS_MD_PATH": md_path,
        "VELOS_PDF_PATH": pdf_path
    }

    page_result = run_script("notion_page_create.py", page_env)

    if page_result.get("ok"):
        print("✅ Page 생성 성공!")
        print(f"   페이지 ID: {page_result.get('page_id')}")
        print(f"   블록 수: {page_result.get('blocks_count')}개")
        page_id = page_result.get("page_id")
    else:
        print("❌ Page 생성 실패:")
        print(f"   오류: {page_result.get('error')}")
        return 1

    # 3단계: 하위 Page 생성 테스트
    print("\n🔹 3단계: 하위 Page 생성 테스트")
    print("-" * 30)

    subpage_env = {
        "NOTION_PARENT_PAGE": page_id,
        "VELOS_TITLE": "VELOS 하위 페이지 테스트",
        "VELOS_MD_PATH": md_path
    }

    subpage_result = run_script("notion_page_create.py", subpage_env)

    if subpage_result.get("ok"):
        print("✅ 하위 Page 생성 성공!")
        print(f"   페이지 ID: {subpage_result.get('page_id')}")
        print(f"   블록 수: {subpage_result.get('blocks_count')}개")
    else:
        print("❌ 하위 Page 생성 실패:")
        print(f"   오류: {subpage_result.get('error')}")
        return 1

    # 최종 결과
    print("\n🎉 모든 테스트 성공!")
    print("=" * 50)
    print("📊 생성된 항목들:")
    print(f"   📋 DB 항목: {db_result.get('url')}")
    print(f"   📄 메인 페이지: {page_result.get('url')}")
    print(f"   📄 하위 페이지: {subpage_result.get('url')}")

    # 통합 결과 JSON
    final_result = {
        "ok": True,
        "test_type": "notion_integrated",
        "results": {
            "database": db_result,
            "page": page_result,
            "subpage": subpage_result
        }
    }

    print(f"\n📋 테스트 결과 JSON:")
    print(json.dumps(final_result, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
