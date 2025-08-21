# [ACTIVE] VELOS Notion 상태 확인 시스템 - Notion DB 상태 검사 스크립트
# -*- coding: utf-8 -*-
"""
Notion DB 상태 옵션 확인 스크립트
"""

import os

import requests
from env_loader import load_env


def main():
    load_env()

    token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DATABASE_ID")

    if not token or not database_id:
        print("❌ 필수 환경변수 누락")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
    }

    try:
        # 데이터베이스 메타데이터 가져오기
        response = requests.get(
            f"https://api.notion.com/v1/databases/{database_id}", headers=headers
        )

        if response.status_code != 200:
            print(f"❌ API 호출 실패: {response.status_code}")
            return

        data = response.json()
        properties = data.get("properties", {})

        print("🔍 Notion DB 상태 옵션 확인")
        print("=" * 40)

        # 상태 속성 찾기
        status_prop = None
        for prop_name, prop_data in properties.items():
            if prop_data.get("type") == "status":
                status_prop = prop_data
                print(f"📊 상태 속성: {prop_name}")
                break

        if status_prop:
            options = status_prop.get("status", {}).get("options", [])
            print(f"✅ 사용 가능한 상태 옵션 ({len(options)}개):")
            for option in options:
                name = option.get("name", "")
                color = option.get("color", "")
                print(f"   • {name} ({color})")
        else:
            print("❌ 상태 속성을 찾을 수 없습니다")

        # 다른 속성들도 확인
        print(f"\n📋 전체 속성 ({len(properties)}개):")
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get("type", "unknown")
            print(f"   • {prop_name} -> {prop_type}")

    except Exception as e:
        print(f"❌ 오류: {e}")


if __name__ == "__main__":
    main()
