# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

"""
UTF-8 인코딩 강제 설정 유틸리티
Python 스크립트에서 일관된 UTF-8 인코딩을 보장합니다.
"""

import sys
import os


def force_utf8_encoding():
    """
    stdout과 stderr을 UTF-8로 강제 설정합니다.
    예외가 발생해도 스크립트 실행을 중단하지 않습니다.
    """
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
        return True
    except Exception:
        # 예외가 발생해도 스크립트 실행을 중단하지 않음
        return False


def setup_utf8_environment():
    """
    UTF-8 환경을 완전히 설정합니다.
    환경 변수와 인코딩을 모두 설정합니다.
    """
    # 환경 변수 설정
    os.environ.setdefault('PYTHONUTF8', '1')
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

    # 인코딩 강제 설정
    success = force_utf8_encoding()

    return success


# 모듈 로드 시 자동으로 UTF-8 설정
if __name__ != "__main__":
    setup_utf8_environment()

# 직접 실행 시 테스트
if __name__ == "__main__":
    print("=== UTF-8 인코딩 테스트 ===")
    print("한글 테스트: 안녕하세요!")
    print("이모지 테스트: 🚀✨🎉")
    print("특수문자 테스트: ©®™")

    success = setup_utf8_environment()
    print(f"UTF-8 설정 성공: {success}")

    # 설정 후 다시 출력
    print("\n=== 설정 후 출력 ===")
    print("한글 테스트: 안녕하세요!")
    print("이모지 테스트: 🚀✨🎉")
    print("특수문자 테스트: ©®™")
