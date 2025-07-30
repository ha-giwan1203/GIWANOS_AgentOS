"""
File: C:/giwanos/core/log_manager.py

설명:
- 로그 폴더 C:/giwanos/logs 생성 보장
- master loop 및 Streamlit 앱에 파일 기반 로깅 유틸 제공
"""

import logging
from pathlib import Path

# 로그 디렉토리 경로
LOG_DIR = Path("C:/giwanos/logs")

def setup_logging(name: str, filename: str):
    """
    로깅 설정 유틸:
    1. 로그 디렉토리 생성
    2. 이름별 파일 핸들러 구성 (UTF-8 인코딩)
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / filename

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 중복 핸들러 방지
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(log_file) 
               for h in logger.handlers):
        fh = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger
