#!config.PROJECT_HOMEbin/env python3
from modules.core import config
"""
init_vector_cache.py   (scripts/init_vector_cache.py)

Vector‑cache 파일이 없거나 1 kB 이하일 때만
`modules.advanced.advanced_vectordb --init-index` 를 호출하여
FAISS & NumPy 인덱스를 자동 구축합니다.

사용:
    python scripts/init_vector_cache.py
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VC_DIR = ROOT / "vector_cache"
CACHE_FILES = [
    VC_DIR / "cache_responses.npy",
    VC_DIR / "embeddings.npy",
    VC_DIR / "local_index.faiss",
]


def cache_ready() -> bool:
    for f in CACHE_FILES:
        if not f.exists() or f.stat().st_size < 1024:
            return False
    return True


def build_cache() -> None:
    print("[init_vector_cache] Building vector cache …")
    subprocess.check_call(
        ["python", "-m", "modules.advanced.advanced_vectordb", "--init-index"],
        cwd=ROOT,
    )
    print("[init_vector_cache] DONE")


def main() -> None:
    if cache_ready():
        print("[init_vector_cache] Cache already present; nothing to do.")
    else:
        build_cache()


if __name__ == "__main__":
    main()



