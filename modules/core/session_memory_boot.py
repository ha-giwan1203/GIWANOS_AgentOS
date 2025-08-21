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

import os
import sys
import time
from typing import Dict, Any

# ROOT 경로 설정
# Path manager imports (Phase 2 standardization)
try:
    from modules.core.path_manager import get_velos_root, get_data_path, get_config_path, get_db_path
except ImportError:
    # Fallback functions for backward compatibility
    def get_velos_root(): return "C:/giwanos"
    def get_data_path(*parts): return os.path.join("C:/giwanos", "data", *parts)
    def get_config_path(*parts): return os.path.join("C:/giwanos", "configs", *parts)
    def get_db_path(): return "C:/giwanos/data/memory/velos.db"

ROOT = get_velos_root() if "get_velos_root" in locals() else "C:/giwanos"
if ROOT not in sys.path:
    sys.path.append(ROOT)

def session_bootstrap() -> Dict[str, Any]:
    """
    세션 시작 시 반드시 호출:
    - 핫버퍼에서 컨텍스트 블록과 강제 규칙 로드
    - 세션 메모리 초기화
    - 정책 검증

    Returns:
        Dict[str, Any]: {"context_block": str, "mandates": Dict[str, Any]}
    """
    try:
        from modules.core.hotbuf_manager import session_bootstrap as hotbuf_bootstrap

        print("[VELOS] Session memory bootstrap starting...")

        # 핫버퍼 부트스트랩 실행
        hotbuf_result = hotbuf_bootstrap()

        # 결과 검증
        if not hotbuf_result or "context_block" not in hotbuf_result:
            raise ValueError("Invalid hotbuf bootstrap result")

        # 세션 메모리 상태 기록
        session_data = {
            "context_block": hotbuf_result.get("context_block", ""),
            "mandates": hotbuf_result.get("mandates", {}),
            "session_start_ts": int(time.time()),
            "hotbuf_created_ts": hotbuf_result.get("created_ts", 0),
            "session_id": f"session_{int(time.time())}"
        }

        # 세션 메모리 저장
        _save_session_memory(session_data)

        print(f"[VELOS] Session bootstrap completed")
        print(f"   Context length: {len(session_data['context_block'])} chars")
        print(f"   Mandates count: {len(session_data['mandates'])}")
        print(f"   Session ID: {session_data['session_id']}")

        return session_data

    except Exception as e:
        print(f"[VELOS] Session bootstrap failed: {e}")

        # 실패 시 기본값 반환
        return {
            "context_block": "<<VELOS_CONTEXT:BEGIN>>\n[ERROR] Session bootstrap failed\n<<VELOS_CONTEXT:END>>",
            "mandates": {
                "FILE_NAMES_IMMUTABLE": True,
                "NO_FAKE_CODE": True,
                "ROOT_FIXED": "C:/giwanos",
                "SELF_TEST_REQUIRED": True,
                "PROMPT_ALWAYS_INCLUDE_CONTEXT": True,
            },
            "session_start_ts": int(time.time()),
            "hotbuf_created_ts": 0,
            "session_id": f"session_error_{int(time.time())}",
            "error": str(e)
        }

def _save_session_memory(session_data: Dict[str, Any]):
    """세션 메모리 상태 저장"""
    try:
        session_dir = os.path.join(ROOT, "data", "sessions")
        os.makedirs(session_dir, exist_ok=True)

        session_file = os.path.join(session_dir, f"{session_data['session_id']}.json")

        import json
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"[VELOS] Failed to save session memory: {e}")

def get_current_session() -> Dict[str, Any]:
    """현재 세션 정보 반환"""
    try:
        from modules.core.hotbuf_manager import load_hotbuf

        hotbuf_data = load_hotbuf()

        return {
            "context_block": hotbuf_data.get("context_block", ""),
            "mandates": hotbuf_data.get("mandates", {}),
            "session_start_ts": int(time.time()),
            "hotbuf_created_ts": hotbuf_data.get("created_ts", 0),
            "session_id": f"current_{int(time.time())}"
        }

    except Exception as e:
        print(f"[VELOS] Failed to get current session: {e}")
        return {}

def validate_session_memory(session_data: Dict[str, Any]) -> bool:
    """세션 메모리 유효성 검증"""
    try:
        # 필수 필드 확인
        required_fields = ["context_block", "mandates", "session_start_ts"]
        for field in required_fields:
            if field not in session_data:
                print(f"[VELOS] Missing required field: {field}")
                return False

        # 컨텍스트 블록 유효성 확인
        context = session_data.get("context_block", "")
        if not context or "<<VELOS_CONTEXT:BEGIN>>" not in context:
            print("[VELOS] Invalid context block")
            return False

        # 강제 규칙 유효성 확인
        mandates = session_data.get("mandates", {})
        if not mandates or not isinstance(mandates, dict):
            print("[VELOS] Invalid mandates")
            return False

        return True

    except Exception as e:
        print(f"[VELOS] Session validation failed: {e}")
        return False
