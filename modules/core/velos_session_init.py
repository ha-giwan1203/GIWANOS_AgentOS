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

"""
VELOS Session Initialization Module
사용자가 제공한 코드를 정리된 형태로 제공합니다.

사용법:
    from modules.core.velos_session_init import init_velos_session
    _hot = init_velos_session()
    VELOS_CONTEXT_BLOCK = _hot["context_block"]
"""

import os
import sys
from typing import Dict, Any

# ROOT 경로 설정
ROOT = "C:/giwanos"
if ROOT not in sys.path:
    sys.path.append(ROOT)

def init_velos_session() -> Dict[str, Any]:
    """
    [VELOS: memory context autoload + policy enforcement]

    세션 시작 시 반드시 호출:
    - 핫버퍼에서 컨텍스트 블록과 강제 규칙 로드
    - 정책 검증
    - 세션 메모리 초기화

    Returns:
        Dict[str, Any]: {"context_block": str, "mandates": Dict[str, Any], ...}
    """
    try:
        from modules.core.session_memory_boot import session_bootstrap
        from modules.core.prompt_policy_enforcer import assert_core_policies

        # 세션 부트스트랩 실행
        _hot = session_bootstrap()  # {"context_block":..., "mandates":...}

        # 핵심 정책 검증
        assert_core_policies(_hot["mandates"], "C:/giwanos")

        return _hot

    except Exception as e:
        print(f"[VELOS] Session initialization failed: {e}")

        # 실패 시 기본값 반환
        return {
            "context_block": "<<VELOS_CONTEXT:BEGIN>>\n[ERROR] Session init failed\n<<VELOS_CONTEXT:END>>",
            "mandates": {
                "FILE_NAMES_IMMUTABLE": True,
                "NO_FAKE_CODE": True,
                "ROOT_FIXED": "C:/giwanos",
                "SELF_TEST_REQUIRED": True,
                "PROMPT_ALWAYS_INCLUDE_CONTEXT": True,
            },
            "session_start_ts": 0,
            "hotbuf_created_ts": 0,
            "session_id": "error_session",
            "error": str(e)
        }

def get_velos_context_block() -> str:
    """
    VELOS 컨텍스트 블록 반환
    """
    _hot = init_velos_session()
    return _hot["context_block"]

def get_velos_mandates() -> Dict[str, Any]:
    """
    VELOS 강제 규칙 반환
    """
    _hot = init_velos_session()
    return _hot["mandates"]

# 사용자 제공 코드와 동일한 인터페이스 제공
def velos_session_bootstrap() -> Dict[str, Any]:
    """
    사용자 제공 코드와 동일한 함수명
    """
    return init_velos_session()
