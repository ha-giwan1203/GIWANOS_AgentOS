# ===== VELOS 공용 로거 설정 =====
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
VELOS 시스템 공용 로거 설정

VELOS 시스템 전체에서 사용할 공용 로거를 설정합니다.
"""

import logging
import os
from datetime import datetime
from pathlib import Path

# 로그 디렉토리 설정
LOG_DIR = Path(
    get_data_path("logs") if "get_data_path" in locals() else "/home/user/webapp/data/logs"
)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 로그 파일 경로
APP_LOG_FILE = LOG_DIR / "app.log"
ERROR_LOG_FILE = LOG_DIR / "error.log"
DEBUG_LOG_FILE = LOG_DIR / "debug.log"


def setup_velos_logger():
    """VELOS 시스템 공용 로거 설정"""

    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # 기존 핸들러 제거 (중복 방지)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 포맷터 설정
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. 콘솔 핸들러 (INFO 레벨)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 2. 파일 핸들러 - 일반 로그 (INFO 레벨)
    file_handler = logging.FileHandler(APP_LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # 3. 파일 핸들러 - 에러 로그 (ERROR 레벨)
    error_handler = logging.FileHandler(ERROR_LOG_FILE, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)

    # 4. 파일 핸들러 - 디버그 로그 (DEBUG 레벨)
    debug_handler = logging.FileHandler(DEBUG_LOG_FILE, encoding="utf-8")
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)
    root_logger.addHandler(debug_handler)

    # VELOS 전용 로거 생성
    velos_logger = logging.getLogger("VELOS")
    velos_logger.setLevel(logging.INFO)

    return velos_logger


def get_velos_logger(name=None):
    """VELOS 로거 인스턴스 반환"""
    if name:
        return logging.getLogger(f"VELOS.{name}")
    return logging.getLogger("VELOS")


def log_system_start():
    """시스템 시작 로그"""
    logger = get_velos_logger("System")
    logger.info("🚀 VELOS 시스템 시작")
    logger.info(f"로그 디렉토리: {LOG_DIR}")
    logger.info(f"로그 파일: {APP_LOG_FILE}")


def log_system_stop():
    """시스템 종료 로그"""
    logger = get_velos_logger("System")
    logger.info("🛑 VELOS 시스템 종료")


# 기본 로거 설정
velos_logger = setup_velos_logger()

# 시스템 시작 로그
log_system_start()

if __name__ == "__main__":
    # 테스트 로그
    logger = get_velos_logger("Test")
    logger.info("✅ VELOS 로거 설정 테스트 성공")
    logger.debug("디버그 메시지 테스트")
    logger.warning("경고 메시지 테스트")
    logger.error("에러 메시지 테스트")

    print(f"로그 파일이 생성되었습니다:")
    print(f"- 일반 로그: {APP_LOG_FILE}")
    print(f"- 에러 로그: {ERROR_LOG_FILE}")
    print(f"- 디버그 로그: {DEBUG_LOG_FILE}")
