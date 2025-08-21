# =========================================================
# VELOS 운영 철학 선언문
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=/home/user/webapp 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================

# Path manager imports (Phase 2 standardization)
try:
    from modules.core.path_manager import (
        get_config_path,
        get_data_path,
        get_db_path,
        get_velos_root,
    )
except ImportError:
    # Fallback functions for backward compatibility
    def get_velos_root():
        return "/home/user/webapp"

    def get_data_path(*parts):
        return os.path.join("/home/user/webapp", "data", *parts)

    def get_config_path(*parts):
        return os.path.join("/home/user/webapp", "configs", *parts)

    def get_db_path():
        return "/home/user/webapp/data/memory/velos.db"


"""
VELOS Runtime State Management Module

런타임 상태 관리를 위한 도구들을 제공합니다.
"""

import os
import sys
import time
from typing import Any, Dict

# ROOT 경로 설정
ROOT = get_velos_root() if "get_velos_root" in locals() else "/home/user/webapp"
if ROOT not in sys.path:
    sys.path.append(ROOT)

# 간소화된 Cursor 상태 관리 모듈 import
try:
    from modules.core.simple_cursor_state import (
        get_cursor_in_use,
    )
    from modules.core.simple_cursor_state import get_runtime_state as simple_get_runtime_state
    from modules.core.simple_cursor_state import (
        set_cursor_in_use,
    )
except ImportError:
    print("Warning: simple_cursor_state 모듈을 찾을 수 없습니다.")
    get_cursor_in_use = None
    set_cursor_in_use = None
    simple_get_runtime_state = None


def reconcile_env_file_state() -> Dict[str, Any]:
    """
    환경변수와 파일 상태를 조정합니다.

    Returns:
        Dict[str, Any]: 조정 결과
    """
    try:
        if get_cursor_in_use is not None:
            cursor_mode = get_cursor_in_use()
            return {
                "file_flag": cursor_mode,
                "env_flag": cursor_mode,
                "expired": False,
                "final": cursor_mode,
            }
        else:
            # 기본 구현
            return {
                "file_flag": False,
                "env_flag": False,
                "expired": True,
                "final": False,
                "error": "simple_cursor_state not available",
            }
    except Exception as e:
        return {
            "file_flag": False,
            "env_flag": False,
            "expired": True,
            "final": False,
            "error": str(e),
        }


def get_runtime_state() -> Dict[str, Any]:
    """
    현재 런타임 상태를 조회합니다.

    Returns:
        Dict[str, Any]: 런타임 상태 정보
    """
    try:
        if simple_get_runtime_state is not None:
            return simple_get_runtime_state()
        else:
            # 기본 구현
            return {
                "cursor_in_use": False,
                "source": "unknown",
                "error": "simple_cursor_state not available",
            }

    except Exception as e:
        return {"error": str(e), "cursor_in_use": False, "source": "unknown"}


def update_health_with_runtime_state(health: Dict[str, Any]) -> Dict[str, Any]:
    """
    헬스 로그에 런타임 상태를 업데이트합니다.

    Args:
        health: 기존 헬스 데이터

    Returns:
        Dict[str, Any]: 업데이트된 헬스 데이터
    """
    try:
        recon = reconcile_env_file_state()
        runtime_state = get_runtime_state()

        health.update(
            {
                "cursor_state_reconciled": True,
                "cursor_state": recon,
                "runtime_state": runtime_state,
                "last_runtime_check": int(time.time()),
            }
        )

        return health

    except Exception as e:
        health.update(
            {
                "cursor_state_reconciled": False,
                "cursor_state_error": str(e),
                "last_runtime_check": int(time.time()),
            }
        )
        return health


if __name__ == "__main__":
    # 자가 검증 테스트
    print("=== VELOS Runtime State 자가 검증 테스트 ===")

    # 1. 상태 조정 테스트
    print("1. 상태 조정 테스트:")
    recon = reconcile_env_file_state()
    print(f"   조정 결과: {recon}")

    # 2. 런타임 상태 조회 테스트
    print("\n2. 런타임 상태 조회 테스트:")
    runtime_state = get_runtime_state()
    print(f"   런타임 상태: {runtime_state}")

    # 3. 헬스 업데이트 테스트
    print("\n3. 헬스 업데이트 테스트:")
    health = {}
    updated_health = update_health_with_runtime_state(health)
    print(f"   업데이트된 헬스: {updated_health}")

    print("\n=== 자가 검증 완료 ===")
