# scripts/notion_payload_min.py
import os, requests, datetime
from pathlib import Path

# --- 환경변수 로딩 ---
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

def mk_props(title):
    # 실제 Notion DB 스키마에 맞춤
    return {"제목": {"title": [{"text": {"content": title}}]}}  # 최소 필수만

def test_minimal_notion():
    """최소 페이로드로 Notion 테스트"""
    token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DATABASE_ID")

    if not token:
        print("❌ NOTION_TOKEN이 설정되지 않았습니다.")
        return False

    if not database_id:
        print("❌ NOTION_DATABASE_ID가 설정되지 않았습니다.")
        return False

    print(f"🔍 Notion 최소 페이로드 테스트")
    print(f"   Database ID: {database_id}")
    print(f"   Token: {token[:10]}..." if token else "Token: None")

    payload = {
        "parent": {"database_id": database_id},
        "properties": mk_props("VELOS Report OK")
    }

    try:
        r = requests.post(
            "https://api.notion.com/v1/pages",
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=10
        )

        print(f"📊 응답 상태: {r.status_code}")
        print(f"📝 응답 내용: {r.text[:200]}")

        if r.status_code < 300:
            print("✅ 성공!")
            return True
        else:
            print("❌ 실패")
            return False

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

if __name__ == "__main__":
    success = test_minimal_notion()
    exit(0 if success else 1)
