# [ACTIVE] scripts/dispatch_notion.py
from __future__ import annotations

import json
import os
import time
from pathlib import Path


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

    from modules.utils.net import post_with_retry
except Exception:
    requests = None
    post_with_retry = None

ROOT = Path(r"C:\giwanos")
AUTO = ROOT / "data" / "reports" / "auto"
DISP = ROOT / "data" / "reports" / "_dispatch"
DISP.mkdir(parents=True, exist_ok=True)


def _env(name, default=None):
    return os.getenv(name, default)


def get_notion_schema(token: str, database_id: str) -> dict:
    """Notion DB 스키마 자동 탐지"""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
        }
        resp = requests.get(
            f"https://api.notion.com/v1/databases/{database_id}", headers=headers, timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("properties", {})
        else:
            print(f"스키마 조회 실패: {resp.status_code}")
            return {}
    except Exception as e:
        print(f"스키마 조회 오류: {e}")
        return {}


def build_notion_props(schema: dict, title: str, pdf_path: Path) -> dict:
    """스키마에 맞는 속성 구성"""
    props = {}

    # 실제 DB 스키마에 맞춤
    props["제목"] = {"title": [{"text": {"content": title}}]}
    props["설명"] = {"rich_text": [{"text": {"content": f"PDF 파일: {pdf_path.name}"}}]}

    # 상태 필드 추가 (있는 경우)
    if "상태" in schema:
        props["상태"] = {"status": {"name": "완료"}}

    # 날짜 필드 추가 (있는 경우)
    if "날짜" in schema:
        from datetime import datetime

        props["날짜"] = {"date": {"start": datetime.now().isoformat()}}

    return props


def send_notion_only(pdf_path: Path, md_path: Path | None, title: str) -> dict:
    """Notion 전용 전송 함수 (자동 스키마 탐지)"""
    if not _env("DISPATCH_NOTION", "1") == "1":
        return {"ok": False, "detail": "disabled", "ts": int(time.time())}

    token = _env("NOTION_TOKEN")
    database_id = _env("NOTION_DATABASE_ID")
    if not (token and database_id):
        return {
            "ok": False,
            "detail": "missing NOTION_TOKEN or NOTION_DATABASE_ID",
            "ts": int(time.time()),
        }
    if requests is None:
        return {"ok": False, "detail": "requests not installed", "ts": int(time.time())}

    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

        # 스키마 자동 탐지
        schema = get_notion_schema(token, database_id)
        if not schema:
            return {"ok": False, "detail": "스키마 탐지 실패", "ts": int(time.time())}

        # 스키마에 맞는 속성 구성
        props = build_notion_props(schema, title, pdf_path)
        if not props:
            return {"ok": False, "detail": "적합한 필드를 찾을 수 없음", "ts": int(time.time())}

        children = []
        if md_path and md_path.exists():
            snippet = (md_path.read_text("utf-8", errors="ignore")[:1200]).strip()
            if snippet:
                children.append(
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": snippet}}]
                        },
                    }
                )

        payload = {
            "parent": {"database_id": database_id},
            "properties": props,
            "children": children,
        }
        resp = (
            post_with_retry(
                "https://api.notion.com/v1/pages",
                headers=headers,
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                retries=2,
            )
            if post_with_retry
            else requests.post(
                "https://api.notion.com/v1/pages",
                headers=headers,
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            )
        )
        ok = resp.status_code < 300
        return {"ok": ok, "detail": f"status={resp.status_code}", "ts": int(time.time())}
    except Exception as e:
        return {"ok": False, "detail": f"exception: {e}", "ts": int(time.time())}


def dispatch_notion():
    """Notion 디스패치 메인 함수"""
    latest = max(AUTO.glob("velos_auto_report_*_ko.pdf"), default=None)
    md = max(AUTO.glob("velos_auto_report_*.md"), default=None)
    if not latest:
        print("no pdf found in", AUTO)
        return False

    title = "VELOS 한국어 보고서"
    result = send_notion_only(latest, md, title)

    # 결과 저장
    out = DISP / f"dispatch_notion_{time.strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    # 결과 출력
    print(json.dumps(result, ensure_ascii=False, indent=2))

    return result["ok"]


if __name__ == "__main__":
    success = dispatch_notion()
    exit(0 if success else 1)
