# [ACTIVE] VELOS Notion 데이터베이스 필드 자동 탐색 스크립트
# 데이터베이스 스키마 분석 + 필드 매핑 자동화
import os
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

def load_env():
    """환경변수 로딩"""
    env_file = Path("configs/.env")
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file, override=True)
            print(f"✅ 환경변수 로딩 완료: {env_file}")
        except Exception as e:
            print(f"⚠️ 환경변수 로딩 실패: {e}")

def get_notion_token() -> Optional[str]:
    """Notion 토큰 가져오기"""
    token = os.getenv("NOTION_TOKEN")
    if not token:
        print("❌ NOTION_TOKEN 환경변수 없음")
        return None
    return token

def get_database_id() -> Optional[str]:
    """데이터베이스 ID 가져오기"""
    db_id = os.getenv("NOTION_DATABASE_ID")
    if not db_id:
        print("❌ NOTION_DATABASE_ID 환경변수 없음")
        return None
    return db_id

def query_database_schema(token: str, database_id: str) -> Dict[str, Any]:
    """데이터베이스 스키마 조회"""
    url = f"https://api.notion.com/v1/databases/{database_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ 데이터베이스 스키마 조회 실패: {e}")
        return {}

def analyze_properties(schema: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """속성 필드 분석"""
    properties = schema.get("properties", {})
    field_analysis = {}
    
    for field_name, field_config in properties.items():
        field_type = field_config.get("type", "unknown")
        field_info = {
            "type": field_type,
            "config": field_config,
            "suggested_mapping": get_suggested_mapping(field_name, field_type, field_config)
        }
        field_analysis[field_name] = field_info
    
    return field_analysis

def get_suggested_mapping(field_name: str, field_type: str, field_config: Dict[str, Any]) -> Dict[str, Any]:
    """필드별 매핑 제안"""
    suggestions = {
        "title": {
            "velos_field": "title",
            "description": "보고서 제목",
            "priority": "high"
        },
        "description": {
            "velos_field": "summary",
            "description": "보고서 요약",
            "priority": "high"
        },
        "date": {
            "velos_field": "created_at",
            "description": "생성 날짜",
            "priority": "medium"
        },
        "select": {
            "velos_field": "category",
            "description": "보고서 카테고리",
            "priority": "medium"
        },
        "multi_select": {
            "velos_field": "tags",
            "description": "태그",
            "priority": "low"
        },
        "rich_text": {
            "velos_field": "content",
            "description": "상세 내용",
            "priority": "high"
        },
        "url": {
            "velos_field": "file_url",
            "description": "파일 링크",
            "priority": "medium"
        },
        "number": {
            "velos_field": "version",
            "description": "버전 번호",
            "priority": "low"
        }
    }
    
    # 필드명 기반 매핑
    field_name_lower = field_name.lower()
    if "title" in field_name_lower or "제목" in field_name_lower:
        return suggestions.get("title", {})
    elif "description" in field_name_lower or "설명" in field_name_lower:
        return suggestions.get("description", {})
    elif "date" in field_name_lower or "날짜" in field_name_lower:
        return suggestions.get("date", {})
    elif "category" in field_name_lower or "카테고리" in field_name_lower:
        return suggestions.get("select", {})
    elif "tag" in field_name_lower or "태그" in field_name_lower:
        return suggestions.get("multi_select", {})
    elif "content" in field_name_lower or "내용" in field_name_lower:
        return suggestions.get("rich_text", {})
    elif "url" in field_name_lower or "링크" in field_name_lower:
        return suggestions.get("url", {})
    elif "version" in field_name_lower or "버전" in field_name_lower:
        return suggestions.get("number", {})
    
    # 타입 기반 기본 매핑
    return suggestions.get(field_type, {
        "velos_field": field_name,
        "description": f"자동 매핑: {field_type}",
        "priority": "low"
    })

def generate_mapping_config(field_analysis: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """매핑 설정 생성"""
    mapping = {
        "database_id": os.getenv("NOTION_DATABASE_ID"),
        "generated_at": datetime.now().isoformat(),
        "fields": {},
        "auto_mapping": True
    }
    
    for field_name, field_info in field_analysis.items():
        mapping["fields"][field_name] = {
            "notion_field": field_name,
            "velos_field": field_info["suggested_mapping"]["velos_field"],
            "type": field_info["type"],
            "priority": field_info["suggested_mapping"]["priority"],
            "description": field_info["suggested_mapping"]["description"]
        }
    
    return mapping

def save_mapping_config(mapping: Dict[str, Any], filename: str = "notion_field_mapping.json"):
    """매핑 설정 저장"""
    config_dir = Path("configs")
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / filename
    config_file.write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✅ 매핑 설정 저장: {config_file}")

def update_dispatch_script(mapping: Dict[str, Any]):
    """dispatch_report.py 스크립트 업데이트"""
    dispatch_file = Path("scripts/dispatch_report.py")
    if not dispatch_file.exists():
        print(f"❌ dispatch_report.py 파일 없음")
        return
    
    # 현재 파일 내용 읽기
    content = dispatch_file.read_text(encoding="utf-8")
    
    # Notion 전송 함수 찾기
    if "def send_notion(" in content:
        print("✅ dispatch_report.py에 Notion 함수 존재")
        
        # 필드 매핑 정보 주석으로 추가
        mapping_comment = "\n".join([
            "# Notion 필드 매핑 정보:",
            "# " + "=" * 50
        ])
        
        for field_name, field_config in mapping["fields"].items():
            mapping_comment += f"\n# {field_name}: {field_config['velos_field']} ({field_config['type']})"
        
        # 주석 추가 위치 찾기
        if "# ---------------- Notion ----------------" in content:
            content = content.replace(
                "# ---------------- Notion ----------------",
                "# ---------------- Notion ----------------\n" + mapping_comment
            )
            
            dispatch_file.write_text(content, encoding="utf-8")
            print("✅ dispatch_report.py에 필드 매핑 정보 추가")
    else:
        print("⚠️ dispatch_report.py에 Notion 함수 없음")

def test_notion_connection(token: str, database_id: str) -> bool:
    """Notion 연결 테스트"""
    url = f"https://api.notion.com/v1/databases/{database_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Notion 연결 성공")
            return True
        else:
            print(f"❌ Notion 연결 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Notion 연결 오류: {e}")
        return False

def main():
    print("🔍 VELOS Notion 데이터베이스 필드 자동 탐색 시작")
    print("=" * 60)
    
    # 1. 환경변수 로딩
    load_env()
    
    # 2. Notion 토큰 및 데이터베이스 ID 확인
    token = get_notion_token()
    database_id = get_database_id()
    
    if not token or not database_id:
        print("❌ 필수 환경변수 누락")
        return
    
    # 3. Notion 연결 테스트
    if not test_notion_connection(token, database_id):
        print("❌ Notion 연결 실패")
        return
    
    # 4. 데이터베이스 스키마 조회
    print("\n📊 데이터베이스 스키마 분석 중...")
    schema = query_database_schema(token, database_id)
    
    if not schema:
        print("❌ 스키마 조회 실패")
        return
    
    # 5. 필드 분석
    field_analysis = analyze_properties(schema)
    
    print(f"\n📋 발견된 필드: {len(field_analysis)}개")
    for field_name, field_info in field_analysis.items():
        mapping = field_info["suggested_mapping"]
        print(f"  • {field_name} ({field_info['type']}) → {mapping['velos_field']}")
    
    # 6. 매핑 설정 생성
    mapping_config = generate_mapping_config(field_analysis)
    
    # 7. 설정 저장
    save_mapping_config(mapping_config)
    
    # 8. dispatch 스크립트 업데이트
    update_dispatch_script(mapping_config)
    
    print("\n" + "=" * 60)
    print("🎉 Notion 필드 자동 탐색 완료!")
    print("✅ 매핑 설정이 configs/notion_field_mapping.json에 저장되었습니다")
    print("✅ dispatch_report.py에 필드 정보가 추가되었습니다")

if __name__ == "__main__":
    main()
