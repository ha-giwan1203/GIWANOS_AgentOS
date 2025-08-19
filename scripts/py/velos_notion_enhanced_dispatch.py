# [ACTIVE] VELOS Notion 향상된 디스패치 스크립트
# 필드 매핑을 활용한 자동 데이터 매핑
import os
import json
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


def load_env():
    """환경변수 로딩"""
    env_file = Path("configs/.env")
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file, override=True)
        except Exception:
            pass


def load_field_mapping() -> Dict[str, Any]:
    """필드 매핑 설정 로드 (수정된 버전 우선)"""
    # 수정된 매핑 파일 우선 시도
    mapping_file = Path("configs/notion_field_mapping_fixed.json")
    if not mapping_file.exists():
        # 기존 매핑 파일 시도
        mapping_file = Path("configs/notion_field_mapping.json")
    
    if mapping_file.exists():
        try:
            return json.loads(mapping_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"⚠️ 매핑 파일 로드 실패: {e}")
    return {}


def create_notion_properties(mapping: Dict[str, Any], report_data: Dict[str, Any]) -> Dict[str, Any]:
    """Notion 속성 생성"""
    properties = {}
    
    for field_name, field_config in mapping.get("fields", {}).items():
        notion_field = field_config["notion_field"]
        velos_field = field_config["velos_field"]
        field_type = field_config["type"]
        
        # VELOS 데이터에서 값 가져오기
        value = report_data.get(velos_field)
        if value is None:
            continue
        
        # 필드 타입별 속성 생성
        if field_type == "title":
            properties[notion_field] = {
                "title": [{"text": {"content": str(value)}}]
            }
        elif field_type == "rich_text":
            properties[notion_field] = {
                "rich_text": [{"text": {"content": str(value)}}]
            }
        elif field_type == "date":
            if isinstance(value, str):
                properties[notion_field] = {"date": {"start": value}}
            else:
                properties[notion_field] = {"date": {"start": datetime.now().isoformat()}}
        elif field_type == "select":
            properties[notion_field] = {"select": {"name": str(value)}}
        elif field_type == "multi_select":
            if isinstance(value, list):
                properties[notion_field] = {
                    "multi_select": [{"name": str(item)} for item in value]
                }
            else:
                properties[notion_field] = {
                    "multi_select": [{"name": str(value)}]
                }
        elif field_type == "number":
            try:
                properties[notion_field] = {"number": float(value)}
            except (ValueError, TypeError):
                continue
        elif field_type == "url":
            properties[notion_field] = {"url": str(value)}
        elif field_type == "status":
            properties[notion_field] = {"status": {"name": str(value)}}
    
    return properties


def send_enhanced_notion_report(
    pdf_path: Path,
    md_path: Optional[Path] = None,
    title: str = "VELOS 보고서"
) -> Dict[str, Any]:
    """향상된 Notion 보고서 전송"""
    
    # 환경변수 확인
    token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DATABASE_ID")
    
    if not token or not database_id:
        return {"ok": False, "detail": "missing NOTION_TOKEN or NOTION_DATABASE_ID"}
    
    # 필드 매핑 로드
    mapping = load_field_mapping()
    if not mapping:
        return {"ok": False, "detail": "field mapping not found"}
    
    # 보고서 데이터 준비
    report_data = {
        "title": title,
        "summary": f"VELOS 보고서: {pdf_path.name}",
        "created_at": datetime.now().isoformat(),
        "category": "VELOS_Report",
        "tags": ["VELOS", "자동생성"],
        "content": "",
        "file_url": str(pdf_path),
        "version": 1.0
    }
    
    # 마크다운 내용 추가
    if md_path and md_path.exists():
        try:
            md_content = md_path.read_text(encoding="utf-8", errors="ignore")
            report_data["content"] = md_content[:2000]  # Notion 제한
        except Exception:
            pass
    
    # Notion 속성 생성
    properties = create_notion_properties(mapping, report_data)
    
    # 필수 필드 확인
    if "제목" not in properties:
        properties["제목"] = {"title": [{"text": {"content": title}}]}
    
    # API 요청
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    payload = {
        "parent": {"database_id": database_id},
        "properties": properties
    }
    
    try:
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "ok": True,
                "detail": f"created page: {result.get('id', 'unknown')}",
                "page_id": result.get("id")
            }
        else:
            return {
                "ok": False,
                "detail": f"API error: {response.status_code} - {response.text[:200]}"
            }
            
    except Exception as e:
        return {"ok": False, "detail": f"request failed: {e}"}


def main():
    """메인 함수"""
    print("🚀 VELOS Notion 향상된 디스패치 테스트")
    print("=" * 50)
    
    # 환경변수 로딩
    load_env()
    
    # 최신 보고서 파일 찾기
    auto_dir = Path("data/reports/auto")
    if not auto_dir.exists():
        print("❌ auto 디렉토리 없음")
        return
    
    pdf_files = list(auto_dir.glob("velos_auto_report_*_ko.pdf"))
    if not pdf_files:
        print("❌ PDF 파일 없음")
        return
    
    latest_pdf = max(pdf_files, key=lambda x: x.stat().st_mtime)
    latest_md = latest_pdf.with_suffix(".md")
    
    print(f"📄 처리할 파일: {latest_pdf.name}")
    
    # 향상된 Notion 전송
    result = send_enhanced_notion_report(
        pdf_path=latest_pdf,
        md_path=latest_md if latest_md.exists() else None,
        title=f"VELOS 보고서 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    
    print(f"\n📊 전송 결과:")
    print(f"  성공: {result['ok']}")
    print(f"  상세: {result['detail']}")
    
    if result.get("page_id"):
        print(f"  페이지 ID: {result['page_id']}")


if __name__ == "__main__":
    main()
