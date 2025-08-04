#!/usr/bin/env python3
"""
path_utils.py   (modules/core/path_utils.py)

❶  저장소 루트(repo_root) 자동 탐색  
❷  주요 리소스 폴더 경로 헬퍼  
❸  OS 간 호환(Pathlib 기반) 경로 생성

사용 예:
    from modules.core.path_utils import FONTS_DIR, font_path
    pdf.render(font_path("Nanum_Gothic/NanumGothic-Regular.ttf"))
"""

from pathlib import Path
import yaml

# ---------------------------------------------------------
# 1) 저장소 루트 = 이 파일에서 세 단계 위 (…/modules/core/ → modules → <repo>)
# ---------------------------------------------------------
REPO_ROOT: Path = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------
# 2) settings.yaml 로부터 커스텀 경로 로드 (있으면 덮어쓰기)
# ---------------------------------------------------------
CONFIG_FILE = REPO_ROOT / "configs" / "settings.yaml"
_DEFAULTS = {
    "fonts_dir": "fonts",
    "snapshots_dir": "data/snapshots",
    "vector_cache_dir": "vector_cache",
}

if CONFIG_FILE.exists():
    with CONFIG_FILE.open(encoding="utf-8") as fp:
        _cfg = yaml.safe_load(fp) or {}
else:
    _cfg = {}

FONTS_DIR: Path = REPO_ROOT / _cfg.get("fonts_dir", _DEFAULTS["fonts_dir"])
SNAPSHOTS_DIR: Path = REPO_ROOT / _cfg.get("snapshots_dir", _DEFAULTS["snapshots_dir"])
VECTOR_CACHE_DIR: Path = REPO_ROOT / _cfg.get("vector_cache_dir", _DEFAULTS["vector_cache_dir"])

# ---------------------------------------------------------
# 3) 헬퍼 함수
# ---------------------------------------------------------
def font_path(rel: str) -> Path:
    """Return absolute Path to a font file under FONTS_DIR."""
    return (FONTS_DIR / rel).resolve()

def snapshot_path(name: str) -> Path:
    """Return absolute Path inside snapshots directory."""
    return (SNAPSHOTS_DIR / name).resolve()

def cache_file(name: str) -> Path:
    """Return absolute Path inside vector_cache directory."""
    return (VECTOR_CACHE_DIR / name).resolve()

# (선택) CLI 테스트
if __name__ == "__main__":
    print("Repo root      :", REPO_ROOT)
    print("Fonts dir      :", FONTS_DIR)
    print("Snapshots dir  :", SNAPSHOTS_DIR)
    print("Vector cache   :", VECTOR_CACHE_DIR)
