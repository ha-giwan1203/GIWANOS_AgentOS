# [ACTIVE] VELOS 호환성 뷰 적용 시스템 - 데이터베이스 뷰 적용 스크립트
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
VELOS 운영 철학 선언문: 파일명은 절대 변경하지 않는다. 수정 시 자가 검증을 포함하고,
실행 결과를 기록하며, 경로/구조는 불변으로 유지한다. 실패는 로깅하고 자동 복구를
시도한다.

호환성 뷰 적용 스크립트
기존 VELOS 스크립트들이 새로운 memory 스키마와 호환되도록 뷰를 생성합니다.
"""

import os
import sqlite3
import sys
from pathlib import Path


def _env(key, default=None):
    """환경 변수 로드 (ENV > configs/settings.yaml > 기본값)"""
    import yaml

    # 1. 환경 변수 확인
    value = os.getenv(key)
    if value:
        return value

    # 2. configs/settings.yaml 확인
    try:
        config_path = Path(__file__).parent.parent / "configs" / "settings.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if config and key in config:
                    return str(config[key])
    except Exception:
        pass

    # 3. 기본값 반환
    return default or "/home/user/webapp"


def apply_compat_views():
    """호환성 뷰를 VELOS DB에 적용"""
    db_path = _env(
        "VELOS_DB_PATH",
        (
            get_db_path()
            if "get_db_path" in locals()
            else (
                get_data_path("memory/velos.db")
                if "get_data_path" in locals()
                else "/home/user/webapp/data/memory/velos.db"
            )
        ),
    )

    print(f"VELOS DB 경로: {db_path}")

    if not os.path.exists(db_path):
        print(f"오류: DB 파일이 존재하지 않습니다: {db_path}")
        return False

    # SQL 파일 읽기
    sql_file = Path(__file__).parent / "sql" / "compat_views.sql"
    if not sql_file.exists():
        print(f"오류: SQL 파일이 존재하지 않습니다: {sql_file}")
        return False

    try:
        with open(sql_file, "r", encoding="utf-8") as f:
            sql_content = f.read()

        # DB 연결 및 뷰 생성
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # 뷰 생성
            for statement in sql_content.split(";"):
                statement = statement.strip()
                if statement and not statement.startswith("--"):
                    print(f"실행: {statement[:50]}...")
                    conn.execute(statement)

            conn.commit()

            # 뷰 확인
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='view'")
            views = [row[0] for row in cursor.fetchall()]
            print(f"생성된 뷰: {views}")

            return True

    except Exception as e:
        print(f"오류: {e}")
        return False


if __name__ == "__main__":
    print("VELOS 호환성 뷰 적용 시작...")
    success = apply_compat_views()

    if success:
        print("✅ 호환성 뷰 적용 완료")
    else:
        print("❌ 호환성 뷰 적용 실패")
        sys.exit(1)
