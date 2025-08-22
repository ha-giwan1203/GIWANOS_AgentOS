# [ACTIVE] VELOS 호환성 뷰 검증 시스템 - 데이터베이스 뷰 검증 스크립트
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
        return "C:\giwanos"

    def get_data_path(*parts):
        return os.path.join("C:\giwanos", "data", *parts)

    def get_config_path(*parts):
        return os.path.join("C:\giwanos", "configs", *parts)

    def get_db_path():
        return "C:\giwanos/data/memory/velos.db"


"""
VELOS 운영 철학 선언문: 파일명은 절대 변경하지 않는다. 수정 시 자가 검증을 포함하고,
실행 결과를 기록하며, 경로/구조는 불변으로 유지한다. 실패는 로깅하고 자동 복구를
시도한다.

호환성 뷰 검증 스크립트
생성된 뷰들이 제대로 작동하는지 확인합니다.
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
    return default or "C:\giwanos"


def check_compat_views():
    """호환성 뷰 검증"""
    db_path = _env(
        "VELOS_DB_PATH",
        (
            get_db_path()
            if "get_db_path" in locals()
            else (
                get_data_path("memory/velos.db")
                if "get_data_path" in locals()
                else "C:\giwanos/data/memory/velos.db"
            )
        ),
    )

    print(f"VELOS DB 경로: {db_path}")

    if not os.path.exists(db_path):
        print(f"오류: DB 파일이 존재하지 않습니다: {db_path}")
        return False

    try:
        with sqlite3.connect(db_path) as conn:
            # 뷰 존재 확인
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='view'")
            views = [row[0] for row in cursor.fetchall()]
            print(f"발견된 뷰: {views}")

            expected_views = ["memory_compat", "memory_roles"]
            missing_views = [v for v in expected_views if v not in views]

            if missing_views:
                print(f"❌ 누락된 뷰: {missing_views}")
                return False

            # 뷰 구조 확인
            for view_name in expected_views:
                print(f"\n=== {view_name} 뷰 검증 ===")

                # 컬럼 정보 확인
                cursor = conn.execute(f"PRAGMA table_info({view_name})")
                columns = [row[1] for row in cursor.fetchall()]
                print(f"컬럼: {columns}")

                # 샘플 데이터 확인
                cursor = conn.execute(f"SELECT * FROM {view_name} LIMIT 3")
                rows = cursor.fetchall()
                print(f"샘플 데이터 ({len(rows)}개):")
                for row in rows:
                    print(f"  {row}")

            return True

    except Exception as e:
        print(f"오류: {e}")
        return False


if __name__ == "__main__":
    print("VELOS 호환성 뷰 검증 시작...")
    success = check_compat_views()

    if success:
        print("\n✅ 호환성 뷰 검증 완료")
    else:
        print("\n❌ 호환성 뷰 검증 실패")
        sys.exit(1)
