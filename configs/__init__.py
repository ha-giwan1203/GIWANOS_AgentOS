# [EXPERIMENT] VELOS 설정 패키지 - 환경 변수 및 설정 관리
# VELOS 운영 철학 선언문
# "판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다."

"""
VELOS 설정 관리 모듈
환경 변수 우선순위: ENV > configs/settings.yaml > 기본값
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

def resolve_env_vars(value: str) -> str:
    """환경 변수를 해석하여 실제 값으로 변환"""
    if not isinstance(value, str) or not value.startswith("${") or not value.endswith("}"):
        return value
    
    # ${VAR:-default} 형식 처리
    var_part = value[2:-1]  # ${...} 제거
    if ":-" in var_part:
        var_name, default_value = var_part.split(":-", 1)
        return os.getenv(var_name, default_value)
    else:
        return os.getenv(var_part, value)

def load_settings() -> Dict[str, Any]:
    """VELOS 설정 로드"""
    settings_path = Path(__file__).parent / "settings.yaml"
    
    if not settings_path.exists():
        return {}
    
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = yaml.safe_load(f)
        
        # 환경 변수 해석
        return _resolve_nested_env_vars(settings)
    except Exception as e:
        print(f"설정 로드 오류: {e}")
        return {}

def _resolve_nested_env_vars(obj: Any) -> Any:
    """중첩된 객체의 환경 변수를 재귀적으로 해석"""
    if isinstance(obj, dict):
        return {key: _resolve_nested_env_vars(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_resolve_nested_env_vars(item) for item in obj]
    elif isinstance(obj, str):
        return resolve_env_vars(obj)
    else:
        return obj

def get_setting(key: str, default: Any = None) -> Any:
    """특정 설정값 조회"""
    settings = load_settings()
    
    # 점 표기법으로 중첩된 키 접근 (예: "database.path")
    keys = key.split('.')
    value = settings
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value

def get_root_path() -> str:
    """VELOS 루트 경로 조회"""
    return get_setting('root', 'C:/giwanos')

def get_db_path() -> str:
    """데이터베이스 경로 조회"""
    return get_setting('database.path', 'data/memory/velos.db')

def get_log_path() -> str:
    """로그 경로 조회"""
    return get_setting('logging.path', 'data/logs')

# 전역 설정 객체
SETTINGS = load_settings()

__all__ = [
    'load_settings',
    'get_setting', 
    'get_root_path',
    'get_db_path',
    'get_log_path',
    'SETTINGS'
]
