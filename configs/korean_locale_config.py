# ===== Korean locale + UTF-8 + font =====
"""
VELOS 한국어 로케일 및 폰트 설정

이 모듈은 VELOS 시스템에서 한국어 처리를 위한 환경 설정을 제공합니다.
"""

import os
import json
import sys
from pathlib import Path

# ===== 환경 변수 설정 =====
def setup_korean_environment():
    """한국어 환경 설정"""
    os.environ.setdefault("VELOS_LANG", "ko")
    os.environ.setdefault("APP_LOCALE", "ko-KR")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("LANG", "ko_KR.UTF-8")
    os.environ.setdefault("LC_ALL", "ko_KR.UTF-8")

# ===== Streamlit 설정 =====
def setup_streamlit_korean():
    """Streamlit 한국어 폰트 설정"""
    try:
        import streamlit as st

        # 페이지 설정
        st.set_page_config(
            page_title="VELOS 대시보드",
            page_icon="🚀",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # 전역 폰트 적용 (없으면 Malgun Gothic으로 폴백)
        st.markdown("""
            <style>
            :root, html, body, .stMarkdown, .stText, .stCodeBlock, .stDataFrame * {
              font-family: "Nanum Gothic", "Malgun Gothic", "Segoe UI", system-ui, sans-serif !important;
            }
            code, pre { font-family: "D2Coding", "Cascadia Code", Consolas, monospace !important; }
            </style>
        """, unsafe_allow_html=True)

        return True
    except ImportError:
        # Streamlit이 설치되지 않은 경우
        return False
    except Exception as e:
        print(f"Streamlit 설정 오류: {e}")
        return False

# ===== JSON 한글 깨짐 방지 =====
def dumps_ko(obj, **kw):
    """
    한국어가 포함된 JSON을 올바르게 출력하는 함수

    Args:
        obj: 직렬화할 객체
        **kw: json.dumps의 추가 인자

    Returns:
        한국어가 포함된 JSON 문자열
    """
    kw.setdefault("ensure_ascii", False)
    kw.setdefault("indent", 2)
    return json.dumps(obj, **kw)

# ===== 로그 설정 =====
def setup_korean_logging():
    """한국어 로깅 설정"""
    try:
        import logging

        # 로깅 포맷터 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            encoding='utf-8'
        )

        # 루트 로거 설정
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # 콘솔 핸들러 설정
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)

        # 파일 핸들러 설정
        log_file = Path("logs/velos_korean.log")
        log_file.parent.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)

        # 핸들러 추가
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

        return True
    except Exception as e:
        print(f"로깅 설정 오류: {e}")
        return False

# ===== 시스템 초기화 =====
def initialize_korean_system():
    """VELOS 시스템 한국어 초기화"""
    print("🇰🇷 VELOS 한국어 시스템 초기화 중...")

    # 환경 변수 설정
    setup_korean_environment()
    print("✅ 환경 변수 설정 완료")

    # Streamlit 설정
    if setup_streamlit_korean():
        print("✅ Streamlit 한국어 설정 완료")
    else:
        print("⚠️ Streamlit 설정 건너뜀 (설치되지 않음)")

    # 로깅 설정
    if setup_korean_logging():
        print("✅ 한국어 로깅 설정 완료")
    else:
        print("⚠️ 로깅 설정 실패")

    print("🎉 VELOS 한국어 시스템 초기화 완료!")

# ===== 사용 예시 =====
if __name__ == "__main__":
    # 시스템 초기화
    initialize_korean_system()

    # JSON 테스트
    test_data = {
        "message": "한국어 테스트 메시지",
        "status": "정상",
        "details": {
            "user": "사용자",
            "action": "실행"
        }
    }

    print("\n📝 JSON 출력 테스트:")
    print(dumps_ko(test_data))
