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

import re
import os
import sys
from typing import Dict, Any, Optional

# ROOT 경로 설정
ROOT = os.getenv("VELOS_ROOT", "/workspace")
if ROOT not in sys.path:
    sys.path.append(ROOT)

HEADER_BEGIN = "<<VELOS_MANDATES:BEGIN>>"
HEADER_END = "<<VELOS_MANDATES:END>>"

def mandates_header(mandates: Dict[str, Any]) -> str:
    """
    강제 규칙을 헤더 형태로 포맷팅
    """
    lines = [HEADER_BEGIN]
    for k, v in mandates.items():
        lines.append(f"{k}={v}")
    lines.append(HEADER_END)
    return "\n".join(lines)

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
            return re.sub(
                pattern,
                replacement,
                system_prompt,
                flags=re.DOTALL
            )
        else:
            # 새로운 헤더 추가
            return mandates_header(mandates) + "\n" + system_prompt

    except Exception as e:
        # 오류 발생 시 원본 프롬프트 반환
        return system_prompt

def assert_core_policies(mandates: Dict[str, Any], root_path: str = ROOT) -> bool:
    """
    핵심 운영 철학 검증
    """
    try:
        assert mandates.get("FILE_NAMES_IMMUTABLE", True), "file names must be immutable"
        assert mandates.get("NO_FAKE_CODE", True), "fake code not allowed"
        assert mandates.get("ROOT_FIXED", os.getenv("VELOS_ROOT", "/workspace")) == root_path, "ROOT mismatch"
        return True
    except AssertionError as e:
        print(f"[VELOS] Core policy violation: {e}")
        return False

def get_mandates_from_hotbuf() -> Dict[str, Any]:
    """
    핫버퍼에서 강제 규칙 로드
    """
    try:
        from modules.core.hotbuf_manager import get_mandates
        return get_mandates()
    except Exception as e:
        # 기본 규칙 반환
        return {
            "FILE_NAMES_IMMUTABLE": True,
            "NO_FAKE_CODE": True,
            "ROOT_FIXED": os.getenv("VELOS_ROOT", "/workspace"),
            "SELF_TEST_REQUIRED": True,
            "PROMPT_ALWAYS_INCLUDE_CONTEXT": True,
        }

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
            return re.sub(
                pattern,
                context,
                system_prompt,
                flags=re.DOTALL
            )
        else:
            # 새로운 컨텍스트 추가
            return context + "\n" + system_prompt

    except Exception as e:
        # 오류 발생 시 원본 프롬프트 반환
        return system_prompt

def create_velos_system_prompt(base_prompt: str = "") -> str:
    """
    VELOS 운영 철학이 주입된 완전한 시스템 프롬프트 생성
    """
    try:
        # 1. 기본 프롬프트 설정
        if not base_prompt:
            base_prompt = """당신은 VELOS 시스템의 AI 어시스턴트입니다.
모든 작업에서 VELOS 운영 철학을 준수해야 합니다."""

        # 2. 강제 규칙 주입
        mandates = get_mandates_from_hotbuf()
        prompt_with_mandates = inject_mandates(base_prompt, mandates)

        # 3. 컨텍스트 주입
        final_prompt = inject_velos_context(prompt_with_mandates)

        # 4. 핵심 정책 검증
        if not assert_core_policies(mandates):
            print("[VELOS] Warning: Core policies validation failed")

        return final_prompt

    except Exception as e:
        print(f"[VELOS] Error creating system prompt: {e}")
        return base_prompt

def validate_mandates_injection(system_prompt: str) -> Dict[str, Any]:
    """
    시스템 프롬프트에 강제 규칙이 올바르게 주입되었는지 검증
    """
    validation_result = {
        "mandates_present": False,
        "context_present": False,
        "mandates_count": 0,
        "context_length": 0,
        "validation_ok": False
    }

    try:
        # 강제 규칙 검증
        if HEADER_BEGIN in system_prompt and HEADER_END in system_prompt:
            validation_result["mandates_present"] = True

            # 강제 규칙 개수 계산
            start_idx = system_prompt.find(HEADER_BEGIN) + len(HEADER_BEGIN)
            end_idx = system_prompt.find(HEADER_END)
            mandates_section = system_prompt[start_idx:end_idx].strip()
            validation_result["mandates_count"] = len([line for line in mandates_section.split('\n') if '=' in line])

        # 컨텍스트 검증
        if "<<VELOS_CONTEXT:BEGIN>>" in system_prompt and "<<VELOS_CONTEXT:END>>" in system_prompt:
            validation_result["context_present"] = True

            # 컨텍스트 길이 계산
            context_start = system_prompt.find("<<VELOS_CONTEXT:BEGIN>>")
            context_end = system_prompt.find("<<VELOS_CONTEXT:END>>") + len("<<VELOS_CONTEXT:END>>")
            context_section = system_prompt[context_start:context_end]
            validation_result["context_length"] = len(context_section)

        # 전체 검증 결과
        validation_result["validation_ok"] = (
            validation_result["mandates_present"] and
            validation_result["context_present"] and
            validation_result["mandates_count"] > 0
        )

        return validation_result

    except Exception as e:
        validation_result["error"] = str(e)
        return validation_result
