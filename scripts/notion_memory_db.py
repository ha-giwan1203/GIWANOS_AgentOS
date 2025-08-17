# scripts/notion_memory_db.py
from __future__ import annotations
import os, json, time, datetime
from pathlib import Path
from typing import Dict, List, Optional

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

try:
    import requests
    from utils.net import post_with_retry
except Exception:
    requests = None
    post_with_retry = None

ROOT = Path(r"C:\giwanos")
MEMORY = ROOT / "data" / "memory"
REFLECTIONS = ROOT / "data" / "reflections"

def _env(name, default=None):
    return os.getenv(name, default)

class NotionMemoryDB:
    """Notion DB 기반 구조화된 기억 저장소"""

    def __init__(self):
        self.token = _env("NOTION_TOKEN")
        self.database_id = _env("NOTION_DATABASE_ID")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

    def create_memory_entry(self,
                          title: str,
                          description: str,
                          tags: List[str] = None,
                          status: str = "완료",
                          source_path: str = None,
                          metadata: str = None) -> Dict:
        """메모리 엔트리 생성"""
        if not (self.token and self.database_id):
            return {"ok": False, "detail": "missing NOTION_TOKEN or NOTION_DATABASE_ID"}

        if requests is None:
            return {"ok": False, "detail": "requests not installed"}

        # 현재 시간 (한국 시간)
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

        # 속성 구성
        props = {
            "제목": {"title": [{"text": {"content": title}}]},
            "설명": {"rich_text": [{"text": {"content": description}}]},
            "날짜": {"date": {"start": now.isoformat()}},
            "상태": {"status": {"name": status}},
        }

        # 태그 추가
        if tags:
            props["태그"] = {"multi_select": [{"name": tag} for tag in tags]}

        # 경로/출처 추가
        if source_path:
            props["경로"] = {"rich_text": [{"text": {"content": source_path}}]}

        # 메타데이터 추가
        if metadata:
            props["메타"] = {"rich_text": [{"text": {"content": metadata}}]}

        payload = {
            "parent": {"database_id": self.database_id},
            "properties": props
        }

        try:
            resp = post_with_retry(
                "https://api.notion.com/v1/pages",
                headers=self.headers,
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                retries=2
            ) if post_with_retry else requests.post(
                "https://api.notion.com/v1/pages",
                headers=self.headers,
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8")
            )

            ok = resp.status_code < 300
            return {
                "ok": ok,
                "detail": f"status={resp.status_code}",
                "page_id": resp.json().get("id") if ok else None,
                "ts": int(time.time())
            }
        except Exception as e:
            return {"ok": False, "detail": f"exception: {e}", "ts": int(time.time())}

    def save_learning_memory(self) -> Dict:
        """learning_memory.jsonl을 Notion DB에 저장"""
        memory_file = MEMORY / "learning_memory.jsonl"
        if not memory_file.exists():
            return {"ok": False, "detail": "learning_memory.jsonl not found"}

        try:
            # 최근 10개 엔트리 읽기
            lines = memory_file.read_text("utf-8").strip().split("\n")[-10:]
            success_count = 0

            for line in lines:
                if not line.strip():
                    continue

                data = json.loads(line)
                title = f"learning_memory_{data.get('ts', int(time.time()))}"
                description = data.get('content', '')[:500]  # 500자 제한
                tags = ["학습", "메모리", "자동"]

                result = self.create_memory_entry(
                    title=title,
                    description=description,
                    tags=tags,
                    source_path=str(memory_file),
                    metadata=f"timestamp: {data.get('ts', 'N/A')}"
                )

                if result["ok"]:
                    success_count += 1

            return {
                "ok": success_count > 0,
                "detail": f"saved {success_count}/{len(lines)} entries",
                "ts": int(time.time())
            }
        except Exception as e:
            return {"ok": False, "detail": f"exception: {e}", "ts": int(time.time())}

    def save_reflection(self) -> Dict:
        """최근 reflection을 Notion DB에 저장"""
        reflection_files = list(REFLECTIONS.glob("reflection_*.json"))
        if not reflection_files:
            return {"ok": False, "detail": "no reflection files found"}

        latest_reflection = max(reflection_files, key=lambda x: x.stat().st_mtime)

        try:
            data = json.loads(latest_reflection.read_text("utf-8-sig"))
            title = f"reflection_{latest_reflection.stem}"
            description = data.get('summary', '')[:500]  # 500자 제한
            tags = ["회고", "리플렉션", "자동"]

            result = self.create_memory_entry(
                title=title,
                description=description,
                tags=tags,
                source_path=str(latest_reflection),
                metadata=f"created: {datetime.datetime.fromtimestamp(latest_reflection.stat().st_mtime).isoformat()}"
            )

            return result
        except Exception as e:
            return {"ok": False, "detail": f"exception: {e}", "ts": int(time.time())}

def main():
    """메인 실행 함수"""
    db = NotionMemoryDB()

    print("🔍 VELOS Notion DB 메모리 저장")
    print("=" * 40)

    # 1. Learning Memory 저장
    print("\n📚 Learning Memory 저장 중...")
    result1 = db.save_learning_memory()
    print(f"결과: {json.dumps(result1, ensure_ascii=False, indent=2)}")

    # 2. Reflection 저장
    print("\n🤔 Reflection 저장 중...")
    result2 = db.save_reflection()
    print(f"결과: {json.dumps(result2, ensure_ascii=False, indent=2)}")

    # 3. 테스트 엔트리 생성
    print("\n🧪 테스트 엔트리 생성 중...")
    result3 = db.create_memory_entry(
        title="VELOS_Notion_DB_Test",
        description="Notion DB 기반 메모리 저장소 테스트",
        tags=["테스트", "VELOS", "Notion"],
        status="완료",
        source_path="scripts/notion_memory_db.py",
        metadata="automated test entry"
    )
    print(f"결과: {json.dumps(result3, ensure_ascii=False, indent=2)}")

    # 결과 요약
    success_count = sum(1 for r in [result1, result2, result3] if r["ok"])
    print(f"\n🎯 성공률: {success_count}/3 ({success_count/3*100:.1f}%)")

    return success_count == 3

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
