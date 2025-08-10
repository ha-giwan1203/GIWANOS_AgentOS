"""
VELOS 운영 철학 선언문
- 파일명 절대 변경 금지 · 모든 수정 후 자가 검증 필수 · 실행 결과 직접 테스트
- 하드코딩 경로 금지: 모든 경로는 환경/설정 기반으로 계산한다.
"""
from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any, Optional

# .env가 있으면 로드(없으면 조용히 무시)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def _auto_root() -> Path:
    # 1) 환경변수 최우선
    env = os.getenv("GIWANOS_ROOT")
    if env:
        return Path(env).expanduser().resolve()

    # 2) 이 파일 기준 상향 탐색
    here = Path(__file__).resolve()
    for p in [here] + list(here.parents):
        if (p / "configs").exists() and (p / "data").exists():
            return p

    # 3) 현재 작업 디렉터리
    return Path.cwd().resolve()


BASE_DIR: Path = _auto_root()


def path(*parts: str, ensure_dir: bool = False) -> Path:
    p = BASE_DIR.joinpath(*parts)
    if ensure_dir:
        p.parent.mkdir(parents=True, exist_ok=True)
    return p


# 표준 경로들
LOG_DIR        = path("data", "logs", ensure_dir=True)
REPORTS_DIR    = path("data", "reports", ensure_dir=True)
MEMORY_DIR     = path("data", "memory", ensure_dir=True)
REFLECTION_DIR = path("data", "reflections", ensure_dir=True)

HEALTH_PATH    = path("data", "logs", "system_health.json")
API_COST_LOG   = path("data", "logs", "api_cost_log.json")
LEARNING_MEMORY = path("data", "memory", "learning_memory.json")


def load_settings() -> dict[str, Any]:
    """configs/settings.json → settings.yaml 순으로 로드"""
    js = path("configs", "settings.json")
    if js.exists():
        try:
            return json.loads(js.read_text(encoding="utf-8"))
        except Exception:
            pass

    yml = path("configs", "settings.yaml")
    if yml.exists():
        try:
            import yaml  # optional
            return yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
        except Exception:
            pass

    return {}


SETTINGS: dict[str, Any] = load_settings()


def get_setting(key: str, default: Optional[Any] = None) -> Any:
    # 1) ENV 2) settings.* 3) default
    if key in os.environ:
        return os.environ[key]
    return SETTINGS.get(key, default)
