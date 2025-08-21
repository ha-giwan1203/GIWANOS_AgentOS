# [ACTIVE] VELOS 운영 철학 선언문
# =========================================================
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

import os
import sys


# Phase 3: VELOS import manager integration for interface package
def _ensure_velos_path():
    """Phase 3 optimized: Use import manager if available, fallback to legacy"""
    try:
        # Try to use import manager
        from modules.core.import_manager import add_velos_path, get_velos_root

        velos_root = str(get_velos_root())
        add_velos_path(velos_root)
        print(f"[interface] Import manager 사용: {velos_root}")
    except ImportError:
        # Fallback to legacy approach
        velos_root = os.environ.get("VELOS_ROOT")
        if velos_root and os.path.isdir(velos_root):
            if velos_root not in sys.path:
                sys.path.insert(0, velos_root)
                print(f"[interface] VELOS_ROOT 추가됨: {velos_root}")
        else:
            # 기본 fallback 경로
            fallback_path = r"/home/user/webapp"
            if os.path.isdir(fallback_path) and fallback_path not in sys.path:
                sys.path.insert(0, fallback_path)
                print(f"[interface] fallback 경로 추가됨: {fallback_path}")


# 모듈 로드 시 자동으로 경로 보장
_ensure_velos_path()


# interface 모듈들의 안전한 임포트를 위한 헬퍼
def safe_import(module_name: str, fallback_func=None):
    """안전한 모듈 임포트 - 실패 시 fallback 함수 반환"""
    try:
        module = __import__(module_name, fromlist=["*"])
        return module
    except ImportError as e:
        print(f"[interface] 임포트 실패: {module_name} - {e}")
        if fallback_func:
            return fallback_func()
        return None
