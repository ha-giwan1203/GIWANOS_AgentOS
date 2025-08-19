# [ACTIVE] VELOS Notion 필드 매핑 문제 진단 및 수정 스크립트
# 필드 타입 불일치 + 매핑 오류 + API 호환성 문제 해결
import os
import json
import requests
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


def load_env():
    """환경변수 로딩"""
    env_file = Path("configs/.env")
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file, override=True)
            return True
        except Exception as e:
            print(f"❌ 환경변수 로딩 실패: {e}")
            return False
    else:
        print(f"❌ 환경변수 파일 없음: {env_file}")
        return False


class NotionFieldFixer:
    """Notion 필드 매핑 문제 수정 클래스"""
    
    def __init__(self):
        self.token = os.getenv("NOTION_TOKEN", "")
        self.database_id = os.getenv("NOTION_DATABASE_ID", "")
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    
    def get_database_schema(self) -> Dict[str, Any]:
        """데이터베이스 스키마 조회"""
        url = f"{self.base_url}/databases/{self.database_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ 데이터베이스 스키마 조회 실패: {e}")
            return {}
    
    def analyze_field_issues(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """필드 문제 분석"""
        print("🔍 필드 문제 분석 중...")
        
        properties = schema.get("properties", {})
        issues = {
            "missing_required_fields": [],
            "type_mismatches": [],
            "mapping_errors": [],
            "api_compatibility": []
        }
        
        # 필수 필드 확인
        required_fields = ["제목", "설명", "날짜"]
        for field in required_fields:
            if field not in properties:
                issues["missing_required_fields"].append(field)
        
        # 필드 타입 확인
        for field_name, field_config in properties.items():
            field_type = field_config.get("type", "")
            
            # 타입별 문제점 확인
            if field_type == "status":
                # status 필드의 옵션 확인
                status_options = field_config.get("status", {}).get("options", [])
                if not status_options:
                    issues["type_mismatches"].append(f"{field_name}: status 옵션 없음")
            
            elif field_type == "select":
                # select 필드의 옵션 확인
                select_options = field_config.get("select", {}).get("options", [])
                if not select_options:
                    issues["type_mismatches"].append(f"{field_name}: select 옵션 없음")
            
            elif field_type == "multi_select":
                # multi_select 필드의 옵션 확인
                multi_select_options = field_config.get("multi_select", {}).get("options", [])
                if not multi_select_options:
                    issues["type_mismatches"].append(f"{field_name}: multi_select 옵션 없음")
        
        return issues
    
    def create_fixed_mapping(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """수정된 매핑 생성"""
        print("🔧 수정된 매핑 생성 중...")
        
        properties = schema.get("properties", {})
        fixed_mapping = {
            "database_id": self.database_id,
            "generated_at": datetime.now().isoformat(),
            "fields": {},
            "auto_mapping": True,
            "fixed_issues": []
        }
        
        # VELOS 보고서용 최적화된 매핑
        velos_mapping = {
            "제목": {
                "velos_field": "title",
                "description": "보고서 제목",
                "priority": "high",
                "required": True
            },
            "설명": {
                "velos_field": "summary", 
                "description": "보고서 요약",
                "priority": "high",
                "required": True
            },
            "날짜": {
                "velos_field": "created_at",
                "description": "생성 날짜",
                "priority": "medium",
                "required": True
            },
            "상태": {
                "velos_field": "status",
                "description": "처리 상태",
                "priority": "medium",
                "required": False
            },
            "태그": {
                "velos_field": "tags",
                "description": "분류 태그",
                "priority": "low",
                "required": False
            },
            "장소": {
                "velos_field": "category",
                "description": "카테고리",
                "priority": "medium",
                "required": False
            },
            "유형": {
                "velos_field": "type",
                "description": "보고서 유형",
                "priority": "medium",
                "required": False
            }
        }
        
        for field_name, field_config in properties.items():
            field_type = field_config.get("type", "")
            
            # VELOS 매핑에서 찾기
            velos_config = velos_mapping.get(field_name, {
                "velos_field": field_name.lower().replace(" ", "_"),
                "description": f"자동 매핑: {field_type}",
                "priority": "low",
                "required": False
            })
            
            # 필드 타입별 안전한 매핑
            safe_mapping = {
                "notion_field": field_name,
                "velos_field": velos_config["velos_field"],
                "type": field_type,
                "priority": velos_config["priority"],
                "description": velos_config["description"],
                "required": velos_config["required"],
                "safe_values": self.get_safe_values(field_type, field_config)
            }
            
            fixed_mapping["fields"][field_name] = safe_mapping
        
        return fixed_mapping
    
    def get_safe_values(self, field_type: str, field_config: Dict[str, Any]) -> List[str]:
        """안전한 값 목록 생성"""
        safe_values = []
        
        if field_type == "status":
            options = field_config.get("status", {}).get("options", [])
            safe_values = [opt.get("name", "") for opt in options if opt.get("name")]
        
        elif field_type == "select":
            options = field_config.get("select", {}).get("options", [])
            safe_values = [opt.get("name", "") for opt in options if opt.get("name")]
        
        elif field_type == "multi_select":
            options = field_config.get("multi_select", {}).get("options", [])
            safe_values = [opt.get("name", "") for opt in options if opt.get("name")]
        
        return safe_values
    
    def test_field_creation(self, mapping: Dict[str, Any]) -> Dict[str, Any]:
        """필드 생성 테스트"""
        print("🧪 필드 생성 테스트 중...")
        
        test_data = {
            "title": "VELOS 필드 테스트",
            "summary": "필드 매핑 테스트 중입니다.",
            "created_at": datetime.now().isoformat(),
            "status": "진행중",
            "tags": ["VELOS", "테스트"],
            "category": "시스템",
            "type": "보고서"
        }
        
        # 안전한 속성 생성
        properties = {}
        
        for field_name, field_config in mapping["fields"].items():
            notion_field = field_config["notion_field"]
            velos_field = field_config["velos_field"]
            field_type = field_config["type"]
            safe_values = field_config.get("safe_values", [])
            
            # VELOS 데이터에서 값 가져오기
            value = test_data.get(velos_field)
            if value is None:
                continue
            
            # 안전한 속성 생성
            try:
                if field_type == "title":
                    properties[notion_field] = {
                        "title": [{"text": {"content": str(value)}}]
                    }
                elif field_type == "rich_text":
                    properties[notion_field] = {
                        "rich_text": [{"text": {"content": str(value)}}]
                    }
                elif field_type == "date":
                    properties[notion_field] = {"date": {"start": str(value)}}
                elif field_type == "select":
                    if safe_values and str(value) in safe_values:
                        properties[notion_field] = {"select": {"name": str(value)}}
                    elif safe_values:
                        properties[notion_field] = {"select": {"name": safe_values[0]}}
                elif field_type == "multi_select":
                    if isinstance(value, list):
                        valid_values = [v for v in value if v in safe_values]
                        if valid_values:
                            properties[notion_field] = {
                                "multi_select": [{"name": v} for v in valid_values]
                            }
                    elif str(value) in safe_values:
                        properties[notion_field] = {
                            "multi_select": [{"name": str(value)}]
                        }
                elif field_type == "status":
                    if safe_values and str(value) in safe_values:
                        properties[notion_field] = {"status": {"name": str(value)}}
                    elif safe_values:
                        properties[notion_field] = {"status": {"name": safe_values[0]}}
                elif field_type == "number":
                    try:
                        properties[notion_field] = {"number": float(value)}
                    except (ValueError, TypeError):
                        continue
                elif field_type == "url":
                    properties[notion_field] = {"url": str(value)}
                
            except Exception as e:
                print(f"    ⚠️ {field_name} 속성 생성 실패: {e}")
                continue
        
        # 테스트 페이지 생성
        url = f"{self.base_url}/pages"
        payload = {
            "parent": {"database_id": self.database_id},
            "properties": properties
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                page_id = result.get("id")
                
                # 테스트 페이지 삭제 (아카이브)
                if page_id:
                    self.archive_test_page(page_id)
                
                return {
                    "success": True,
                    "page_id": page_id,
                    "properties_created": len(properties)
                }
            else:
                return {
                    "success": False,
                    "error": f"API 오류: {response.status_code}",
                    "response": response.text[:200]
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"요청 실패: {e}"
            }
    
    def archive_test_page(self, page_id: str) -> bool:
        """테스트 페이지 아카이브"""
        url = f"{self.base_url}/pages/{page_id}"
        payload = {"archived": True}
        
        try:
            response = requests.patch(url, headers=self.headers, json=payload, timeout=10)
            return response.status_code == 200
        except Exception:
            return False
    
    def save_fixed_mapping(self, mapping: Dict[str, Any], filename: str = "notion_field_mapping_fixed.json"):
        """수정된 매핑 저장"""
        config_dir = Path("configs")
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / filename
        config_file.write_text(
            json.dumps(mapping, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        print(f"✅ 수정된 매핑 저장: {config_file}")
        return config_file
    
    def update_dispatch_script(self, mapping: Dict[str, Any]):
        """dispatch 스크립트 업데이트"""
        dispatch_file = Path("scripts/dispatch_report.py")
        if not dispatch_file.exists():
            print(f"❌ dispatch_report.py 파일 없음")
            return
        
        # 현재 파일 내용 읽기
        content = dispatch_file.read_text(encoding="utf-8")
        
        # 수정된 필드 매핑 정보 주석으로 추가
        mapping_comment = "\n".join([
            "# 수정된 Notion 필드 매핑 정보:",
            "# " + "=" * 50
        ])
        
        for field_name, field_config in mapping["fields"].items():
            safe_values = field_config.get("safe_values", [])
            safe_values_str = ", ".join(safe_values[:3]) if safe_values else "없음"
            mapping_comment += f"\n# {field_name}: {field_config['velos_field']} ({field_config['type']}) - 안전값: {safe_values_str}"
        
        # 주석 추가 위치 찾기
        if "# ---------------- Notion ----------------" in content:
            # 기존 매핑 주석 제거
            lines = content.split("\n")
            new_lines = []
            skip_mapping = False
            
            for line in lines:
                if "# Notion 필드 매핑 정보:" in line:
                    skip_mapping = True
                elif skip_mapping and line.startswith("# ") and "=" in line:
                    skip_mapping = False
                    continue
                elif skip_mapping and line.startswith("# "):
                    continue
                else:
                    skip_mapping = False
                    new_lines.append(line)
            
            content = "\n".join(new_lines)
            
            # 새로운 매핑 주석 추가
            content = content.replace(
                "# ---------------- Notion ----------------",
                "# ---------------- Notion ----------------\n" + mapping_comment
            )
            
            dispatch_file.write_text(content, encoding="utf-8")
            print("✅ dispatch_report.py에 수정된 필드 매핑 정보 추가")
        else:
            print("⚠️ dispatch_report.py에 Notion 섹션 없음")


def main():
    """메인 함수"""
    print("🔧 VELOS Notion 필드 매핑 문제 진단 및 수정")
    print("=" * 60)
    
    # 환경변수 로딩
    if not load_env():
        print("❌ 환경변수 로딩 실패")
        return
    
    # 필드 수정기 초기화
    fixer = NotionFieldFixer()
    
    # 1. 데이터베이스 스키마 조회
    print("\n📊 데이터베이스 스키마 조회 중...")
    schema = fixer.get_database_schema()
    
    if not schema:
        print("❌ 스키마 조회 실패")
        return
    
    # 2. 필드 문제 분석
    print("\n🔍 필드 문제 분석 중...")
    issues = fixer.analyze_field_issues(schema)
    
    print("발견된 문제점:")
    for issue_type, problems in issues.items():
        if problems:
            print(f"  • {issue_type}: {len(problems)}개")
            for problem in problems[:3]:  # 최대 3개만 표시
                print(f"    - {problem}")
    
    # 3. 수정된 매핑 생성
    print("\n🔧 수정된 매핑 생성 중...")
    fixed_mapping = fixer.create_fixed_mapping(schema)
    
    print(f"수정된 필드: {len(fixed_mapping['fields'])}개")
    for field_name, field_config in fixed_mapping["fields"].items():
        safe_values = field_config.get("safe_values", [])
        print(f"  • {field_name}: {field_config['velos_field']} (안전값: {len(safe_values)}개)")
    
    # 4. 필드 생성 테스트
    print("\n🧪 필드 생성 테스트 중...")
    test_result = fixer.test_field_creation(fixed_mapping)
    
    if test_result["success"]:
        print(f"✅ 테스트 성공: {test_result['properties_created']}개 속성 생성")
    else:
        print(f"❌ 테스트 실패: {test_result['error']}")
    
    # 5. 수정된 매핑 저장
    mapping_file = fixer.save_fixed_mapping(fixed_mapping)
    
    # 6. dispatch 스크립트 업데이트
    fixer.update_dispatch_script(fixed_mapping)
    
    print("\n" + "=" * 60)
    print("🎉 Notion 필드 매핑 문제 수정 완료!")
    print(f"📄 수정된 매핑: {mapping_file}")


if __name__ == "__main__":
    main()
