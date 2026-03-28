# [EXPERIMENT] scripts/notion_schema_check.py
import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# 환경변수 로딩
def _load_dotenv():
    try:
        from dotenv import load_dotenv
    except Exception:
        return
    root = Path(r"C:\giwanos")
    for p in (root/"configs/.env", root/".env"):
        if p.exists():
            load_dotenv(dotenv_path=p, override=False, encoding="utf-8")
_load_dotenv()

def check_notion_schema():
    token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DATABASE_ID")

    if not token:
        print("❌ NOTION_TOKEN이 설정되지 않았습니다.")
        return

    if not database_id:
        print("❌ NOTION_DATABASE_ID가 설정되지 않았습니다.")
        return

    print(f"🔍 Notion 데이터베이스 스키마 확인 중...")
    print(f"   Database ID: {database_id}")
    print(f"   Token: {token[:10]}..." if token else "Token: None")

    try:
        # 데이터베이스 메타데이터 조회
        meta = requests.get(
            f"https://api.notion.com/v1/databases/{database_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": "2022-06-28",
            }
        )

        if meta.status_code != 200:
            print(f"❌ 데이터베이스 조회 실패: {meta.status_code}")
            print(f"   응답: {meta.text}")
            return

        meta_data = meta.json()
        props = meta_data.get("properties", {})

        print("\n=== Notion DB Properties ===")
        print(f"데이터베이스 제목: {meta_data.get('title', [{}])[0].get('text', {}).get('content', 'N/A')}")
        print(f"속성 개수: {len(props)}")
        print()

        for k, v in props.items():
            prop_type = v.get("type", "unknown")
            print(f"  {k} -> {prop_type}")

            # 속성 타입별 상세 정보
            if prop_type == "title":
                print(f"    (제목 속성 - 필수)")
            elif prop_type == "rich_text":
                print(f"    (텍스트 속성)")
            elif prop_type == "select":
                options = v.get("select", {}).get("options", [])
                print(f"    (선택 속성 - 옵션: {len(options)}개)")
            elif prop_type == "multi_select":
                options = v.get("multi_select", {}).get("options", [])
                print(f"    (다중 선택 속성 - 옵션: {len(options)}개)")

        print("\n=== 권장 설정 ===")
        title_props = [k for k, v in props.items() if v.get("type") == "title"]
        text_props = [k for k, v in props.items() if v.get("type") == "rich_text"]

        if title_props:
            print(f"✅ 제목 속성: {title_props[0]} (사용 가능)")
        else:
            print("❌ 제목 속성이 없습니다. 'Name' 또는 'Title' 속성을 추가하세요.")

        if text_props:
            print(f"✅ 텍스트 속성: {text_props[0]} (사용 가능)")
        else:
            print("❌ 텍스트 속성이 없습니다. 'Description' 속성을 추가하세요.")

        # dispatch_report.py 수정 제안
        print("\n=== dispatch_report.py 수정 제안 ===")
        if title_props and text_props:
            print("다음과 같이 수정하세요:")
            print(f'props = {{')
            print(f'    "{title_props[0]}": {{"title": [{{"text": {{"content": title}}}}]}},')
            print(f'    "{text_props[0]}": {{"rich_text": [{{"text": {{"content": f"PDF 파일: {{pdf_path.name}}"}}}}]}},')
            print(f'}}')
        else:
            print("필요한 속성이 없습니다. Notion 데이터베이스에 다음 속성을 추가하세요:")
            print("- 제목 속성 (title): 'Name' 또는 'Title'")
            print("- 텍스트 속성 (rich_text): 'Description'")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    check_notion_schema()



