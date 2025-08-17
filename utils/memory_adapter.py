# VELOS 운영 철학 선언문: 파일명은 절대 변경하지 않는다. 수정 시 자가 검증을 포함하고,
# 실행 결과를 기록하며, 경로/구조는 불변으로 유지한다. 실패는 로깅하고 자동 복구를 시도한다.

# 기존 코드 호환성을 위한 루트 레벨 memory_adapter.py
# modules.core.memory_adapter 패키지의 주요 함수들을 재export

from importlib import import_module

m = import_module("modules.core.memory_adapter")
MemoryAdapter = m.MemoryAdapter
create_memory_adapter = m.create_memory_adapter
search_by_role = m.search_by_role
normalize_query = m.normalize_query

__all__ = [
    "MemoryAdapter",
    "create_memory_adapter",
    "search_by_role",
    "normalize_query"
]
