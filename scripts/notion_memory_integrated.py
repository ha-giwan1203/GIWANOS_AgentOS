# [ACTIVE] VELOS Notion 메모리 통합 - Notion 메모리 동기화 시스템
# -*- coding: utf-8 -*-
"""
VELOS 운영 철학 선언문
"판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다."

VELOS Notion 메모리 통합 스크립트
- DB 기반 구조화된 기억 저장
- Page 기반 전문 저장
- 통합된 메모리 동기화
"""

import datetime
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional


# --- 환경변수 로딩 ---
def _load_dotenv():
    try:
        from dotenv import load_dotenv
    except Exception:
        return
    root = Path(r"C:\giwanos")
    for p in (root / "configs/.env", root / ".env"):
        if p.exists():
            load_dotenv(dotenv_path=p, override=False, encoding="utf-8")


_load_dotenv()

try:
    import requests
except ImportError:
    requests = None

try:
    from modules.utils.net import post_with_retry
except ImportError:
    post_with_retry = None

ROOT = Path(r"C:\giwanos")
MEMORY = ROOT / "data" / "memory"
REFLECTIONS = ROOT / "data" / "reflections"
REPORTS = ROOT / "data" / "reports"


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

    def create_memory_entry(
        self,
        title: str,
        description: str,
        tags: List[str] = None,
        status: str = "완료",
        source_path: str = None,
        metadata: str = None,
    ) -> Dict:
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

        payload = {"parent": {"database_id": self.database_id}, "properties": props}

        try:
            resp = (
                post_with_retry(
                    "https://api.notion.com/v1/pages",
                    headers=self.headers,
                    data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                    retries=2,
                )
                if post_with_retry
                else requests.post(
                    "https://api.notion.com/v1/pages",
                    headers=self.headers,
                    data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                )
            )

            ok = resp.status_code < 300
            return {
                "ok": ok,
                "page_id": resp.json().get("id") if ok else None,
                "page_url": (
                    f"https://notion.so/{resp.json().get('id').replace('-', '')}" if ok else None
                ),
                "detail": resp.text if not ok else "success",
            }

        except Exception as e:
            return {"ok": False, "detail": str(e)}


class NotionMemoryPage:
    """Notion Page 기반 전문 저장소"""

    def __init__(self):
        self.token = _env("NOTION_TOKEN")
        self.database_id = _env("NOTION_DATABASE_ID")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

    def create_report_page(
        self, title: str, content: str, report_type: str = "보고서", source_file: str = None
    ) -> Dict:
        """보고서 전문 페이지 생성"""
        if not (self.token and self.database_id):
            return {"ok": False, "detail": "missing NOTION_TOKEN or NOTION_DATABASE_ID"}

        if requests is None:
            return {"ok": False, "detail": "requests not installed"}

        # 현재 시간 (한국 시간)
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

        # 기본 속성
        props = {
            "제목": {"title": [{"text": {"content": title}}]},
            "설명": {"rich_text": [{"text": {"content": f"{report_type} 전문 저장"}}]},
            "날짜": {"date": {"start": now.isoformat()}},
            "상태": {"status": {"name": "완료"}},
            "태그": {"multi_select": [{"name": report_type}, {"name": "전문"}, {"name": "VELOS"}]},
        }

        if source_file:
            props["경로"] = {"rich_text": [{"text": {"content": source_file}}]}

        # 페이지 내용 (블록)
        children = []

        # 제목 블록
        children.append(
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": title}}]},
            }
        )

        # 메타데이터 블록
        children.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"생성 시간: {now.strftime('%Y-%m-%d %H:%M:%S')}"},
                        },
                        {"type": "text", "text": {"content": f" | 타입: {report_type}"}},
                        {"type": "text", "text": {"content": f" | 소스: {source_file or 'N/A'}"}},
                    ]
                },
            }
        )

        # 구분선
        children.append({"object": "block", "type": "divider", "divider": {}})

        # 2000자마다 블록 분할 (Notion 제한)
        content_blocks = self._split_content_to_blocks(content)
        children.extend(content_blocks)

        payload = {
            "parent": {"database_id": self.database_id},
            "properties": props,
            "children": children,
        }

        try:
            resp = (
                post_with_retry(
                    "https://api.notion.com/v1/pages",
                    headers=self.headers,
                    data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                    retries=2,
                )
                if post_with_retry
                else requests.post(
                    "https://api.notion.com/v1/pages",
                    headers=self.headers,
                    data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                )
            )

            ok = resp.status_code < 300
            return {
                "ok": ok,
                "page_id": resp.json().get("id") if ok else None,
                "page_url": (
                    f"https://notion.so/{resp.json().get('id').replace('-', '')}" if ok else None
                ),
                "detail": resp.text if not ok else "success",
            }

        except Exception as e:
            return {"ok": False, "detail": str(e)}

    def _split_content_to_blocks(self, content: str, max_length: int = 2000) -> List[Dict]:
        """내용을 Notion 블록으로 분할"""
        blocks = []

        # 내용이 너무 길면 잘라내기
        if len(content) > 50000:
            content = content[:50000] + "\n\n[내용이 잘렸습니다...]"

        # 문단 단위로 분할
        paragraphs = content.split("\n")
        current_block = ""

        for para in paragraphs:
            if len(current_block) + len(para) > max_length:
                if current_block:
                    blocks.append(
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {"type": "text", "text": {"content": current_block.strip()}}
                                ]
                            },
                        }
                    )
                current_block = para
            else:
                current_block += "\n" + para if current_block else para

        # 마지막 블록 추가
        if current_block.strip():
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": current_block.strip()}}]
                    },
                }
            )

        return blocks


def sync_learning_memory():
    """learning_memory.jsonl을 Notion DB에 저장"""
    print("📊 learning_memory.jsonl을 Notion DB에 저장 중...")

    db = NotionMemoryDB()
    memory_file = MEMORY / "learning_memory.jsonl"

    if not memory_file.exists():
        print("❌ learning_memory.jsonl 파일이 없습니다")
        return False

    try:
        with open(memory_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        success_count = 0
        for line in lines:
            try:
                data = json.loads(line.strip())
                title = data.get("title", "Unknown")
                content = data.get("content", "")
                tags = data.get("tags", [])

                result = db.create_memory_entry(
                    title=title,
                    description=content[:200] + "..." if len(content) > 200 else content,
                    tags=tags,
                    source_path="learning_memory.jsonl",
                )

                if result["ok"]:
                    success_count += 1
                else:
                    print(f"⚠️  실패: {title} - {result['detail']}")

            except Exception as e:
                print(f"⚠️  파싱 오류: {e}")

        print(f"✅ {success_count}/{len(lines)} 개 메모리 저장 완료")
        return success_count > 0

    except Exception as e:
        print(f"❌ 메모리 저장 실패: {e}")
        return False


def sync_reflections():
    """최근 reflection을 Notion DB에 저장"""
    print("📊 최근 reflection을 Notion DB에 저장 중...")

    db = NotionMemoryDB()
    reflection_files = list(REFLECTIONS.glob("reflection_*.json"))

    if not reflection_files:
        print("❌ reflection 파일이 없습니다")
        return False

    # 최신 파일 5개만 처리
    latest_files = sorted(reflection_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]

    success_count = 0
    for file_path in latest_files:
        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)

            title = f"Reflection: {file_path.stem}"
            content = data.get("insight", "")
            tags = data.get("tags", [])

            result = db.create_memory_entry(
                title=title,
                description=content[:200] + "..." if len(content) > 200 else content,
                tags=tags,
                source_path=str(file_path.name),
            )

            if result["ok"]:
                success_count += 1
            else:
                print(f"⚠️  실패: {title} - {result['detail']}")

        except Exception as e:
            print(f"⚠️  파싱 오류: {file_path.name} - {e}")

    print(f"✅ {success_count}/{len(latest_files)} 개 reflection 저장 완료")
    return success_count > 0


def sync_latest_report():
    """최신 VELOS 보고서를 Notion Page로 저장"""
    print("📄 최신 VELOS 보고서를 Notion Page로 저장 중...")

    page = NotionMemoryPage()

    # 최신 보고서 찾기
    auto_dir = REPORTS / "auto"
    if not auto_dir.exists():
        print("❌ auto 보고서 디렉토리가 없습니다")
        return False

    md_files = list(auto_dir.glob("velos_auto_report_*.md"))
    if not md_files:
        print("❌ VELOS 보고서 파일이 없습니다")
        return False

    latest_md = max(md_files, key=lambda x: x.stat().st_mtime)

    try:
        with open(latest_md, "r", encoding="utf-8") as f:
            content = f.read()

        title = f"VELOS 보고서: {latest_md.stem}"

        result = page.create_report_page(
            title=title, content=content, report_type="자동보고서", source_file=str(latest_md.name)
        )

        if result["ok"]:
            print(f"✅ 보고서 저장 완료: {result['page_url']}")
            return True
        else:
            print(f"❌ 보고서 저장 실패: {result['detail']}")
            return False

    except Exception as e:
        print(f"❌ 보고서 저장 오류: {e}")
        return False


def main():
    """메인 실행 함수"""
    print("🧠 VELOS Notion 기억 저장소 통합 동기화")
    print("=" * 50)

    # 환경변수 확인
    if not (_env("NOTION_TOKEN") and _env("NOTION_DATABASE_ID")):
        print("❌ NOTION_TOKEN 또는 NOTION_DATABASE_ID가 설정되지 않았습니다")
        return False

    results = {}

    # 1. learning_memory.jsonl 동기화
    print("\n📊 1단계: learning_memory.jsonl 동기화")
    results["learning_memory"] = sync_learning_memory()

    # 2. reflection 동기화
    print("\n📊 2단계: reflection 동기화")
    results["reflections"] = sync_reflections()

    # 3. 최신 보고서 동기화
    print("\n📄 3단계: 최신 보고서 동기화")
    results["latest_report"] = sync_latest_report()

    # 결과 요약
    print("\n📊 동기화 결과 요약")
    print("=" * 30)

    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    for component, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{status} {component}")

    print(f"\n🎯 성공률: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")

    if success_count == total_count:
        print("\n🎉 모든 동기화 완료!")
        return True
    elif success_count > 0:
        print("\n⚠️  부분적 동기화 완료")
        return True
    else:
        print("\n💥 모든 동기화 실패")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
