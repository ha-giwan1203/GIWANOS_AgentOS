# [ACTIVE] VELOS 표준 데이터베이스 연결 유틸리티
# VELOS 운영 철학 선언문: 파일명은 절대 변경하지 않는다. 수정 시 자가 검증을 포함하고,
# 실행 결과를 기록하며, 경로/구조는 불변으로 유지한다. 실패는 로깅하고 자동 복구를 시도한다.

import os
import sqlite3


def db_open(path=None):
    """
    VELOS 표준 데이터베이스 연결 생성
    
    Args:
        path: 데이터베이스 파일 경로 (None이면 환경변수 또는 기본값 사용)
    
    Returns:
        sqlite3.Connection: 최적화된 설정이 적용된 데이터베이스 연결
    """
    if path is None:
        # Use path manager for cross-platform compatibility
        try:
            from .path_manager import get_db_path
            db = get_db_path()
        except ImportError:
            # Fallback to environment variable
            db = os.environ.get("VELOS_DB_PATH", r"C:\giwanos\data\memory\velos.db")
    else:
        db = path
    
    conn = sqlite3.connect(db, timeout=5, isolation_level=None)
    
    # SQLite 성능 최적화 PRAGMA 설정
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.execute("PRAGMA foreign_keys=ON;")
    
    return conn
