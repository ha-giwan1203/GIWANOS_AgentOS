# scripts/notion_memory_page.py
from __future__ import annotations
import os, json, time, datetime
from pathlib import Path
from typing import Dict, List

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
REPORTS = ROOT / "data" / "reports"
MEMORY = ROOT / "data" / "memory"

def _env(name, default=None):
    return os.getenv(name, default)

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

    def create_report_page(self,
                          title: str,
                          content: str,
                          report_type: str = "보고서",
                          source_file: str = None) -> Dict:
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
        children.append({
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": title}}]
            }
        })

        # 메타데이터 블록
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": f"생성 시간: {now.strftime('%Y-%m-%d %H:%M:%S')}"}},
                    {"type": "text", "text": {"content": f" | 타입: {report_type}"}},
                    {"type": "text", "text": {"content": f" | 소스: {source_file or 'N/A'}"}}
                ]
            }
        })

        # 구분선
        children.append({
            "object": "block",
            "type": "divider",
            "divider": {}
        })

        # 내용 블록 (긴 텍스트는 여러 블록으로 분할)
        content_lines = content.split('\n')
        current_block = []

        for line in content_lines:
            current_block.append(line)

            # 2000자마다 블록 분할 (Notion 제한)
            if len('\n'.join(current_block)) > 2000:
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": '\n'.join(current_block)}}]
                    }
                })
                current_block = []

        # 남은 내용 추가
        if current_block:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": '\n'.join(current_block)}}]
                }
            })

        payload = {
            "parent": {"database_id": self.database_id},
            "properties": props,
            "children": children
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
                "page_url": f"https://notion.so/{resp.json().get('id').replace('-', '')}" if ok else None,
                "ts": int(time.time())
            }
        except Exception as e:
            return {"ok": False, "detail": f"exception: {e}", "ts": int(time.time())}

    def save_latest_report(self) -> Dict:
        """최신 VELOS 보고서를 Notion Page로 저장"""
        # PDF 보고서 찾기
        pdf_files = list(REPORTS.glob("**/velos_auto_report_*_ko.pdf"))
        if not pdf_files:
            return {"ok": False, "detail": "no VELOS PDF reports found"}

        latest_pdf = max(pdf_files, key=lambda x: x.stat().st_mtime)

        # MD 파일 찾기
        md_file = latest_pdf.with_suffix('.md')
        if not md_file.exists():
            return {"ok": False, "detail": f"MD file not found: {md_file}"}

        try:
            content = md_file.read_text("utf-8")
            title = f"VELOS 보고서 - {latest_pdf.stem}"

            result = self.create_report_page(
                title=title,
                content=content,
                report_type="VELOS_보고서",
                source_file=str(latest_pdf)
            )

            return result
        except Exception as e:
            return {"ok": False, "detail": f"exception: {e}", "ts": int(time.time())}

    def save_learning_memory_full(self) -> Dict:
        """learning_memory.jsonl 전체를 Notion Page로 저장"""
        memory_file = MEMORY / "learning_memory.jsonl"
        if not memory_file.exists():
            return {"ok": False, "detail": "learning_memory.jsonl not found"}

        try:
            content = memory_file.read_text("utf-8")
            title = f"VELOS Learning Memory - {datetime.datetime.now().strftime('%Y%m%d')}"

            result = self.create_report_page(
                title=title,
                content=content,
                report_type="학습_메모리",
                source_file=str(memory_file)
            )

            return result
        except Exception as e:
            return {"ok": False, "detail": f"exception: {e}", "ts": int(time.time())}

    def save_reflection_full(self) -> Dict:
        """최근 reflection 전체를 Notion Page로 저장"""
        reflection_files = list(ROOT.glob("data/reflections/reflection_*.json"))
        if not reflection_files:
            return {"ok": False, "detail": "no reflection files found"}

        latest_reflection = max(reflection_files, key=lambda x: x.stat().st_mtime)

        try:
            content = latest_reflection.read_text("utf-8-sig")
            title = f"VELOS Reflection - {latest_reflection.stem}"

            result = self.create_report_page(
                title=title,
                content=content,
                report_type="회고_리플렉션",
                source_file=str(latest_reflection)
            )

            return result
        except Exception as e:
            return {"ok": False, "detail": f"exception: {e}", "ts": int(time.time())}

def main():
    """메인 실행 함수"""
    page = NotionMemoryPage()

    print("🔍 VELOS Notion Page 전문 저장")
    print("=" * 40)

    # 1. 최신 보고서 저장
    print("\n📊 최신 VELOS 보고서 저장 중...")
    result1 = page.save_latest_report()
    print(f"결과: {json.dumps(result1, ensure_ascii=False, indent=2)}")

    # 2. Learning Memory 전문 저장
    print("\n📚 Learning Memory 전문 저장 중...")
    result2 = page.save_learning_memory_full()
    print(f"결과: {json.dumps(result2, ensure_ascii=False, indent=2)}")

    # 3. Reflection 전문 저장
    print("\n🤔 Reflection 전문 저장 중...")
    result3 = page.save_reflection_full()
    print(f"결과: {json.dumps(result3, ensure_ascii=False, indent=2)}")

    # 4. 테스트 페이지 생성
    print("\n🧪 테스트 페이지 생성 중...")
    test_content = """# VELOS Notion Page 테스트

이것은 VELOS Notion Page 기반 전문 저장소의 테스트 페이지입니다.

## 기능
- 보고서 전문 저장
- 학습 메모리 전체 저장
- 회고 리플렉션 저장
- 자동 태그 분류

## 생성 시간
{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 상태
✅ 테스트 완료
"""

    result4 = page.create_report_page(
        title="VELOS_Notion_Page_Test",
        content=test_content,
        report_type="테스트",
        source_file="scripts/notion_memory_page.py"
    )
    print(f"결과: {json.dumps(result4, ensure_ascii=False, indent=2)}")

    # 결과 요약
    success_count = sum(1 for r in [result1, result2, result3, result4] if r["ok"])
    print(f"\n🎯 성공률: {success_count}/4 ({success_count/4*100:.1f}%)")

    # 성공한 페이지 URL 출력
    for i, result in enumerate([result1, result2, result3, result4], 1):
        if result["ok"] and result.get("page_url"):
            print(f"📄 페이지 {i} URL: {result['page_url']}")

    return success_count == 4

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
