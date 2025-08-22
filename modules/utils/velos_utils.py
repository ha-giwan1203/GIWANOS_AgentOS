# [ACTIVE] VELOS 유틸리티 - 공통 기능 모듈
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VELOS 운영 철학 선언문: 파일명은 절대 변경하지 않는다. 수정 시 자가 검증을 포함하고,
실행 결과를 기록하며, 경로/구조는 불변으로 유지한다. 실패는 로깅하고 자동 복구를
시도한다.

VELOS 공통 유틸리티
성능 측정, 안전한 계산, 로깅 등의 공통 기능을 제공합니다.
"""

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

# 공통 상수
EPS = 1e-9  # 1ns


def now_ns() -> int:
    """현재 시간을 나노초 단위로 반환"""
    return time.perf_counter_ns()


def elapsed_s(t0_ns: int) -> float:
    """경과 시간을 초 단위로 반환 (0 방지)"""
    dt = (now_ns() - t0_ns) / 1e9
    return dt if dt > EPS else EPS


def safe_ratio(a: float, b: float) -> float:
    """안전한 나눗셈 (0으로 나누기 방지)"""
    return a / max(b, EPS)


def _env(key: str, default: Optional[str] = None) -> str:
    """환경 변수 로드 (ENV > configs/settings.yaml > 기본값)"""
    import yaml

    # 1. 환경 변수 확인
    value = os.getenv(key)
    if value:
        return value

    # 2. configs/settings.yaml 확인
    try:
        config_path = Path(__file__).parent.parent.parent / "configs" / "settings.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if config and key in config:
                    return str(config[key])
    except Exception:
        pass

    # 3. 기본값 반환
    return default or "C:\giwanos"


def add_module_path(relative_path: str) -> None:
    """모듈 경로를 sys.path에 안전하게 추가"""
    try:
        module_path = Path(__file__).parent.parent / relative_path
        if str(module_path) not in sys.path:
            sys.path.insert(0, str(module_path))
    except Exception:
        pass


def safe_import(module_name: str, fallback_path: Optional[str] = None) -> Optional[Any]:
    """안전한 모듈 임포트 (실패 시 None 반환)"""
    try:
        if fallback_path:
            add_module_path(fallback_path)
        return __import__(module_name)
    except ImportError:
        return None


def log_with_timestamp(message: str, level: str = "INFO") -> None:
    """타임스탬프와 함께 로그 출력"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")


def measure_time(func):
    """함수 실행 시간 측정 데코레이터"""

    def wrapper(*args, **kwargs):
        start_ns = now_ns()
        try:
            result = func(*args, **kwargs)
            elapsed = elapsed_s(start_ns)
            log_with_timestamp(f"{func.__name__} 완료: {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = elapsed_s(start_ns)
            log_with_timestamp(f"{func.__name__} 실패 ({elapsed:.3f}s): {e}", "ERROR")
            raise

    return wrapper


def check_file_exists(file_path: str, create_dir: bool = True) -> bool:
    """파일 존재 확인 (디렉토리 생성 옵션)"""
    path = Path(file_path)
    if not path.exists():
        if create_dir and path.parent:
            path.parent.mkdir(parents=True, exist_ok=True)
        return False
    return True


def get_db_path() -> str:
    """VELOS DB 경로 반환"""
    return _env("VELOS_DB_PATH", "C:\giwanos/data/memory/velos.db")


def get_jsonl_dir() -> str:
    """VELOS JSONL 디렉토리 경로 반환"""
    return _env("VELOS_JSONL_DIR", "C:\giwanos/data/memory")


if __name__ == "__main__":
    # 자가 검증
    print("VELOS 유틸리티 자가 검증 시작...")

    # 시간 측정 테스트
    start = now_ns()
    time.sleep(0.1)
    elapsed = elapsed_s(start)
    print(f"시간 측정: {elapsed:.3f}s")

    # 안전한 나눗셈 테스트
    print(f"안전한 나눗셈: {safe_ratio(10, 2)}")
    print(f"0으로 나누기 방지: {safe_ratio(10, 0)}")

    # 경로 테스트
    print(f"DB 경로: {get_db_path()}")
    print(f"JSONL 디렉토리: {get_jsonl_dir()}")

    print("✅ 자가 검증 완료")
