# =========================================================
# VELOS 운영 철학 선언문
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=C:/giwanos 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================
#!/usr/bin/env python3
"""
VELOS Environment Loader
Loads environment variables from .env file or sets defaults
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional

def load_env_file(env_path: Path) -> Dict[str, str]:
    """Load environment variables from .env file"""
    env_vars = {}

    if not env_path.exists():
        return env_vars

    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
    except Exception as e:
        print(f"Warning: Could not load .env file: {e}")

    return env_vars

def setup_velos_env(root_path: Optional[str] = None) -> Dict[str, str]:
    """Setup VELOS environment variables"""

    # Determine root path
    if root_path is None:
        root_path = os.getenv('VELOS_ROOT', 'C:/giwanos')

    root = Path(root_path)

    # Default environment variables
    default_env = {
        'VELOS_ROOT': str(root),
        'VELOS_MODE': 'dev',
        'VELOS_REPORT_DIR': str(root / 'data' / 'reports'),
        'EMAIL_ENABLED': '0',
        'VELOS_DB_PATH': str(root / 'data' / 'velos.db'),
        'VELOS_MEMORY_DB_PATH': str(root / 'data' / 'memory' / 'velos_memory.db'),
        'VELOS_LOG_LEVEL': 'INFO',
        'VELOS_LOG_FILE': str(root / 'logs' / 'velos.log')
    }

    # Load from .env file if it exists
    env_file = root / '.env'
    file_env = load_env_file(env_file)

    # Merge environment variables (file overrides defaults)
    final_env = {**default_env, **file_env}

    # Set environment variables
    for key, value in final_env.items():
        os.environ[key] = value

    return final_env

def get_velos_env(key: str, default: Optional[str] = None) -> str:
    """Get a VELOS environment variable"""
    return os.getenv(key, default)

def print_velos_env():
    """Print current VELOS environment variables"""
    velos_keys = [k for k in os.environ.keys() if k.startswith('VELOS_')]
    velos_keys.extend(['EMAIL_ENABLED'])

    print("VELOS Environment Variables:")
    for key in sorted(velos_keys):
        value = os.getenv(key, 'NOT_SET')
        print(f"  {key}: {value}")

if __name__ == "__main__":
    # Setup environment
    env_vars = setup_velos_env()

    # Print environment
    print_velos_env()

    # Test environment
    print(f"\nTest: VELOS_ROOT = {get_velos_env('VELOS_ROOT')}")
    print(f"Test: VELOS_MODE = {get_velos_env('VELOS_MODE')}")
