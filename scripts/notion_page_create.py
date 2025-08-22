# [ACTIVE] VELOS Notion 페이지 생성 시스템 - Notion 페이지 생성 스크립트
# -*- coding: utf-8 -*-
"""
VELOS Notion Page 생성 스크립트
- Markdown 내용을 Notion 블록으로 변환
- PDF 파일 경로 첨부 지원
- DB 또는 Page 하위에 생성 가능
- 환경변수 기반 유연한 설정
"""

import json
import os
import sys
from pathlib import Path

import requests

# 환경변수 로딩
try:
    from env_loader import load_env

    load_env()
except ImportError:
    print("⚠️  env_loader 모듈을 찾을 수 없습니다", file=sys.stderr)
    sys.exit(1)


def notion_headers():
    """Notion API 헤더 생성"""
    return {
        "Authorization": f"Bearer {os.getenv('NOTION_TOKEN')}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def md_to_blocks(md_text, max_length=20000):
    """Markdown 텍스트를 Notion 블록으로 변환"""
    blocks = []

    # 텍스트 길이 제한
    if len(md_text) > max_length:
        md_text = md_text[:max_length] + "\n\n[내용이 잘렸습니다...]"

    # 문단 단위로 분할하여 paragraph 블록 생성
    for para in md_text.splitlines():
        para = para.strip()
        if not para:
            # 빈 줄은 빈 paragraph 블록으로 생성
            blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": []}})
        else:
            # 일반 텍스트는 paragraph 블록으로 생성
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": para}}]},
                }
            )

    return blocks


def create_file_link_block(file_path, file_type="PDF"):
    """파일 링크 블록 생성"""
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {"type": "text", "text": {"content": f"📎 {file_type} 파일: {file_path}"}}
            ]
        },
    }


def main():
    """메인 실행 함수"""
    print("🚀 VELOS Notion Page 생성 시작")
    print("=" * 40)

    # 필수 환경변수 검증
    token = os.getenv("NOTION_TOKEN")
    parent_page = os.getenv("NOTION_PARENT_PAGE")
    database_id = os.getenv("NOTION_DATABASE_ID")

    if not token:
        print("❌ NOTION_TOKEN이 설정되지 않았습니다", file=sys.stderr)
        sys.exit(2)

    if not (parent_page or database_id):
        print("❌ NOTION_PARENT_PAGE 또는 NOTION_DATABASE_ID가 필요합니다", file=sys.stderr)
        sys.exit(2)

    # 입력값 설정
    title = os.getenv("VELOS_TITLE", "VELOS 자동 보고서")
    md_path = os.getenv("VELOS_MD_PATH", "")
    pdf_path = os.getenv("VELOS_PDF_PATH", "")

    print("📝 생성 정보:")
    print(f"   제목: {title}")
    print(f"   MD 파일: {md_path or '없음'}")
    print(f"   PDF 파일: {pdf_path or '없음'}")
    print(f"   부모: {'Page' if parent_page else 'Database'}")

    # 부모 설정 (우선순위: parent_page > database_id)
    if parent_page:
        parent = {"page_id": parent_page}
        title_prop = "title"  # Page 하위는 단순 title 구조
    else:
        parent = {"database_id": database_id}
        title_prop = "제목"  # DB는 실제 속성명 사용

    # 페이지 생성
    print("\n📄 페이지 생성 중...")

    properties = {"title": [{"type": "text", "text": {"content": title}}]}

    payload = {"parent": parent, "properties": {title_prop: properties["title"]}}

    try:
        r = requests.post(
            "https://api.notion.com/v1/pages", headers=notion_headers(), json=payload, timeout=15
        )

        if r.status_code not in (200, 201):
            print(f"❌ Notion Page 생성 실패: {r.status_code}", file=sys.stderr)
            print(f"   응답: {r.text[:400]}", file=sys.stderr)
            sys.exit(1)

        page = r.json()
        page_id = page["id"]

        print(f"✅ 페이지 생성 성공! ID: {page_id}")

        # 본문 블록 추가
        blocks = []

        # Markdown 내용 추가
        if md_path and os.path.exists(md_path):
            print("📝 Markdown 내용 추가 중...")
            try:
                with open(md_path, "r", encoding="utf-8", errors="ignore") as f:
                    md_text = f.read()

                md_blocks = md_to_blocks(md_text)
                blocks.extend(md_blocks)
                print(f"   ✅ {len(md_blocks)}개 블록 추가")

            except Exception as e:
                print(f"   ⚠️  MD 파일 읽기 실패: {e}")

        # PDF 파일 링크 추가
        if pdf_path and os.path.exists(pdf_path):
            print("📎 PDF 파일 링크 추가 중...")
            file_block = create_file_link_block(pdf_path, "PDF")
            blocks.append(file_block)
            print("   ✅ PDF 링크 추가")

        # 블록 추가 실행
        if blocks:
            print(f"\n📤 {len(blocks)}개 블록 업로드 중...")

            br = requests.patch(
                f"https://api.notion.com/v1/blocks/{page_id}/children",
                headers=notion_headers(),
                json={"children": blocks},
                timeout=20,
            )

            if br.status_code not in (200, 201):
                print(f"❌ 블록 추가 실패: {br.status_code}", file=sys.stderr)
                print(f"   응답: {br.text[:400]}", file=sys.stderr)
                # 페이지는 생성되었으므로 경고만 출력
                print("⚠️  페이지는 생성되었지만 내용 추가에 실패했습니다", file=sys.stderr)
            else:
                print("✅ 모든 블록 추가 완료!")

        # 결과 출력
        result = {
            "ok": True,
            "page_id": page_id,
            "title": title,
            "url": f"https://notion.so/{page_id.replace('-', '')}",
            "blocks_count": len(blocks),
            "parent_type": "page" if parent_page else "database",
        }

        print(f"\n🎉 Notion Page 생성 완료!")
        print(f"   URL: {result['url']}")
        print(f"   블록 수: {result['blocks_count']}개")

        # stdout에 JSON 출력 (다음 단계에서 활용)
        print(json.dumps(result, ensure_ascii=False))

        return 0

    except requests.exceptions.Timeout:
        print("❌ Notion API 타임아웃", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ Notion API 오류: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
