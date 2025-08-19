# [EXPERIMENT] VELOS 유틸리티 패키지 - 공통 기능 모듈
# [EXPERIMENT] VELOS 운영 철학 선언문
# "판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다."

"""
VELOS utils 모듈
네트워크, 인코딩, 메모리 어댑터 등의 유틸리티 함수들을 제공합니다.
"""

# 주요 유틸리티 모듈들을 import하여 패키지 레벨에서 접근 가능하게 함
from .net import post_with_retry, get_with_retry, check_connectivity
from .utf8_force import setup_utf8_environment, force_utf8_encoding
from .memory_adapter import MemoryAdapter, normalize_query, create_memory_adapter, search_by_role

__all__ = [
    # net 모듈
    'post_with_retry',
    'get_with_retry', 
    'check_connectivity',
    
    # utf8_force 모듈
    'setup_utf8_environment',
    'force_utf8_encoding',
    
    # memory_adapter 모듈
    'MemoryAdapter',
    'normalize_query',
    'create_memory_adapter',
    'search_by_role'
]

