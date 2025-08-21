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

import os
import re
import sys
from typing import Any, Dict, Optional

# ROOT 경로 설정
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


ROOT = get_velos_root() if "get_velos_root" in locals() else "/home/user/webapp"
if ROOT not in sys.path:
    sys.path.append(ROOT)

HEADER_BEGIN = "<<VELOS_MANDATES:BEGIN>>"
HEADER_END = "<<VELOS_MANDATES:END>>"


def inject_mandates(system_prompt: str, mandates: Dict[str, Any]) -> str:
    """
    시스템 프롬프트에 강제 규칙 주입
    중복 삽입 방지 및 기존 헤더 교체 기능 포함
    """
    try:
        # 중복 삽입 방지
        if HEADER_BEGIN in system_prompt and HEADER_END in system_prompt:
            # 기존 헤더를 최신으로 교체
            pattern = re.escape(HEADER_BEGIN) + r".*?" + re.escape(HEADER_END)
            replacement = mandates_header(mandates)
            return re.sub(pattern, replacement, system_prompt, flags=re.DOTALL)
        else:
            # 새로운 헤더 추가
            return mandates_header(mandates) + "\n" + system_prompt

    except Exception as e:
        print(f"[VELOS] Mandates injection failed: {e}")
        # 오류 발생 시 원본 프롬프트 반환
        return system_prompt


def mandates_header(mandates: Dict[str, Any]) -> str:
    """
    강제 규칙을 헤더 형태로 포맷팅
    """
    lines = [HEADER_BEGIN]
    for k, v in mandates.items():
        lines.append(f"{k}={v}")
    lines.append(HEADER_END)
    return "\n".join(lines)


def assert_core_policies(mandates: Dict[str, Any], root_path: str = ROOT) -> bool:
    """
    핵심 운영 철학 검증
    """
    try:
        # 필수 정책 검증
        assert mandates.get("FILE_NAMES_IMMUTABLE", True), "file names must be immutable"
        assert mandates.get("NO_FAKE_CODE", True), "fake code not allowed"
        assert mandates.get("ROOT_FIXED", "/home/user/webapp") == root_path, "ROOT mismatch"

        # 추가 정책 검증
        assert mandates.get("SELF_TEST_REQUIRED", True), "self-test required"
        assert mandates.get("PROMPT_ALWAYS_INCLUDE_CONTEXT", True), "context must be included"

        print("[VELOS] Core policies validation passed")
        return True

    except AssertionError as e:
        print(f"[VELOS] Core policy violation: {e}")
        return False
    except Exception as e:
        print(f"[VELOS] Policy validation error: {e}")
        return False


def enforce_velos_policies(system_prompt: str, mandates: Dict[str, Any]) -> str:
    """
    VELOS 정책을 시스템 프롬프트에 강제 적용
    """
    try:
        # 1. 핵심 정책 검증
        if not assert_core_policies(mandates):
            print("[VELOS] Warning: Core policies validation failed")

        # 2. 강제 규칙 주입
        prompt_with_mandates = inject_mandates(system_prompt, mandates)

        # 3. 컨텍스트 주입 (필요한 경우)
        if mandates.get("PROMPT_ALWAYS_INCLUDE_CONTEXT", True):
            prompt_with_mandates = inject_velos_context(prompt_with_mandates)

        return prompt_with_mandates

    except Exception as e:
        print(f"[VELOS] Policy enforcement failed: {e}")
        return system_prompt


def inject_velos_context(system_prompt: str) -> str:
    """
    VELOS 컨텍스트를 시스템 프롬프트에 주입
    """
    try:
        from modules.core.hotbuf_manager import get_context_block

        context = get_context_block()

        # 컨텍스트가 이미 포함되어 있는지 확인
        if "<<VELOS_CONTEXT:BEGIN>>" in system_prompt:
            return system_prompt

        # 컨텍스트 주입
        context_header = "<<VELOS_CONTEXT:BEGIN>>"
        context_footer = "<<VELOS_CONTEXT:END>>"

        if context_header in system_prompt and context_footer in system_prompt:
            # 기존 컨텍스트 교체
            pattern = re.escape(context_header) + r".*?" + re.escape(context_footer)
            return re.sub(pattern, context, system_prompt, flags=re.DOTALL)
        else:
            # 새로운 컨텍스트 추가
            return context + "\n" + system_prompt

    except Exception as e:
        print(f"[VELOS] Context injection failed: {e}")
        # 오류 발생 시 원본 프롬프트 반환
        return system_prompt


def validate_policy_enforcement(system_prompt: str) -> Dict[str, Any]:
    """
    정책 강제 적용 결과 검증
    """
    validation_result = {
        "mandates_present": False,
        "context_present": False,
        "mandates_count": 0,
        "context_length": 0,
        "policy_enforcement_ok": False,
    }

    try:
        # 강제 규칙 검증
        if HEADER_BEGIN in system_prompt and HEADER_END in system_prompt:
            validation_result["mandates_present"] = True

            # 강제 규칙 개수 계산
            start_idx = system_prompt.find(HEADER_BEGIN) + len(HEADER_BEGIN)
            end_idx = system_prompt.find(HEADER_END)
            mandates_section = system_prompt[start_idx:end_idx].strip()
            validation_result["mandates_count"] = len(
                [line for line in mandates_section.split("\n") if "=" in line]
            )

        # 컨텍스트 검증
        if "<<VELOS_CONTEXT:BEGIN>>" in system_prompt and "<<VELOS_CONTEXT:END>>" in system_prompt:
            validation_result["context_present"] = True

            # 컨텍스트 길이 계산
            context_start = system_prompt.find("<<VELOS_CONTEXT:BEGIN>>")
            context_end = system_prompt.find("<<VELOS_CONTEXT:END>>") + len("<<VELOS_CONTEXT:END>>")
            context_section = system_prompt[context_start:context_end]
            validation_result["context_length"] = len(context_section)

        # 전체 검증 결과
        validation_result["policy_enforcement_ok"] = (
            validation_result["mandates_present"]
            and validation_result["context_present"]
            and validation_result["mandates_count"] > 0
        )

        return validation_result

    except Exception as e:
        validation_result["error"] = str(e)
        return validation_result


def create_velos_enforced_prompt(
    base_prompt: str = "", mandates: Optional[Dict[str, Any]] = None
) -> str:
    """
    VELOS 정책이 강제 적용된 완전한 시스템 프롬프트 생성
    """
    try:
        # 1. 기본 프롬프트 설정
        if not base_prompt:
            base_prompt = """당신은 VELOS 시스템의 AI 어시스턴트입니다.
모든 작업에서 VELOS 운영 철학을 준수해야 합니다."""

        # 2. 강제 규칙 로드 (제공되지 않은 경우)
        if not mandates:
            from modules.core.hotbuf_manager import get_mandates

            mandates = get_mandates()

        # 3. 정책 강제 적용
        final_prompt = enforce_velos_policies(base_prompt, mandates)

        return final_prompt

    except Exception as e:
        print(f"[VELOS] Error creating enforced prompt: {e}")
        return base_prompt
