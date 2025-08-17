# -*- coding: utf-8 -*-
"""
VELOS Notion DB 생성 스크립트
- REPORT_KEY를 포함한 메타데이터 저장
- 중복 실행 방지 및 결과 추적
- 환경변수 기반 유연한 설정
"""

import os
import sys
import json
import datetime
import requests
from pathlib import Path

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


def build_props(title, path, status, date_iso, tags, report_key=None):
    """Notion DB 속성 구성"""
    # 기본 속성
    T = os.getenv("NOTION_TITLE_PROP", "제목")
    P = os.getenv("NOTION_PATH_PROP", "경로")
    S = os.getenv("NOTION_STATUS_PROP", "상태")
    D = os.getenv("NOTION_DATE_PROP", "날짜")
    G = os.getenv("NOTION_TAGS_PROP", "태그")
    K = os.getenv("NOTION_RESULTID_PROP", "결과 ID")  # REPORT_KEY 저장용

    props = {
        T: {"title": [{"text": {"content": title}}]},
        P: {"rich_text": [{"text": {"content": path or ""}}]},
        S: {"status": {"name": status or "완료"}},
        D: {"date": {"start": date_iso}},
        G: {"multi_select": [{"name": t} for t in (tags or [])]},
    }

    # REPORT_KEY가 있으면 결과 ID 속성에 추가
    if report_key:
        props[K] = {"rich_text": [{"text": {"content": report_key}}]}

    return props


def check_existing_report(report_key):
    """기존 REPORT_KEY 존재 확인"""
    if not report_key:
        return None

    db_id = os.getenv("NOTION_DATABASE_ID")
    if not db_id:
        return None

    try:
        # DB에서 REPORT_KEY 검색
        search_payload = {
            "filter": {
                "property": os.getenv("NOTION_RESULTID_PROP", "결과 ID"),
                "rich_text": {
                    "equals": report_key
                }
            }
        }

        response = requests.post(
            f"https://api.notion.com/v1/databases/{db_id}/query",
            headers=notion_headers(),
            json=search_payload,
            timeout=15
        )

        if response.status_code == 200:
            results = response.json().get("results", [])
            if results:
                return results[0]  # 첫 번째 결과 반환

        return None

    except Exception as e:
        print(f"⚠️  기존 리포트 확인 실패: {e}")
        return None


def main():
    """메인 실행 함수"""
    print("🚀 VELOS Notion DB 생성 시작")
    print("=" * 40)

    # 필수 환경변수 검증
    db_id = os.getenv("NOTION_DATABASE_ID")
    if not db_id or not os.getenv("NOTION_TOKEN"):
        print("❌ NOTION 환경변수가 부족합니다", file=sys.stderr)
        print("   NOTION_TOKEN, NOTION_DATABASE_ID 필요", file=sys.stderr)
        sys.exit(2)

    # REPORT_KEY 확인
    report_key = os.getenv("REPORT_KEY")
    if report_key:
        print(f"📋 REPORT_KEY: {report_key}")

        # 기존 리포트 확인
        existing_report = check_existing_report(report_key)
        if existing_report:
            print("⚠️  이미 존재하는 REPORT_KEY입니다!")
            print(f"   기존 페이지 ID: {existing_report.get('id')}")
            print(f"   기존 제목: {existing_report.get('properties', {}).get('제목', {}).get('title', [{}])[0].get('text', {}).get('content', 'N/A')}")

            # 기존 결과 반환
            result = {
                "ok": True,
                "page_id": existing_report.get('id'),
                "title": existing_report.get('properties', {}).get('제목', {}).get('title', [{}])[0].get('text', {}).get('content', 'N/A'),
                "status": "이미 존재",
                "report_key": report_key,
                "created_at": existing_report.get('created_time'),
                "message": "기존 리포트가 이미 존재합니다"
            }
            print(json.dumps(result, ensure_ascii=False))
            return 0

    # 입력값 설정
    title = os.getenv("VELOS_TITLE", "VELOS 자동 보고서")
    path = os.getenv("VELOS_REPORT_PATH", "")
    status = os.getenv("VELOS_STATUS", "완료")
    tags = (os.getenv("VELOS_TAGS", "Auto,VELOS").split(",") if os.getenv("VELOS_TAGS") else ["Auto", "VELOS"])
    now_iso = datetime.datetime.now().astimezone().isoformat()

    print("📝 생성 정보:")
    print(f"   제목: {title}")
    print(f"   경로: {path}")
    print(f"   상태: {status}")
    print(f"   태그: {', '.join(tags)}")
    print(f"   날짜: {now_iso}")
    if report_key:
        print(f"   결과 ID: {report_key}")

    # 페이로드 생성
    payload = {
        "parent": {"database_id": db_id},
        "properties": build_props(title, path, status, now_iso, [t.strip() for t in tags], report_key),
    }

    print("📤 Notion API 호출 중...")

    try:
        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers=notion_headers(),
            json=payload,
            timeout=15
        )

        if response.status_code not in (200, 201):
            print("❌ Notion DB 생성 실패:", file=sys.stderr)
            print(f"   상태 코드: {response.status_code}", file=sys.stderr)
            print(f"   오류: {response.text[:400]}", file=sys.stderr)
            sys.exit(1)

        data = response.json()
        page_id = data.get("id")

        print("✅ Notion DB 생성 성공!")
        print(f"   페이지 ID: {page_id}")
        print(f"   URL: https://notion.so/{page_id.replace('-', '')}")

        # 성공 결과 JSON
        success_result = {
            "ok": True,
            "page_id": page_id,
            "title": title,
            "status": status,
            "tags": tags,
            "created_at": now_iso,
            "report_key": report_key,
            "url": f"https://notion.so/{page_id.replace('-', '')}"
        }

        print(json.dumps(success_result, ensure_ascii=False))
        return 0

    except requests.exceptions.RequestException as e:
        print("❌ Notion API 요청 실패:", file=sys.stderr)
        print(f"   오류: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print("❌ 예상치 못한 오류:", file=sys.stderr)
        print(f"   오류: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
