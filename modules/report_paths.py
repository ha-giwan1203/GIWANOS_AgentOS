# VELOS 운영: report_paths (호환 고정판)
# - 상단에서 ROOT, P를 반드시 내보냄 (legacy 코드 호환)

from __future__ import annotations
import json
from typing import Dict
from pathlib import Path
import os

# 공통 유틸 가져오기
from modules.velos_common import paths as _paths, ensure_dirs as _ensure_dirs, env_presence as _env_presence

# --- Export: 레거시 호환 필수 심볼 ---
P: Dict[str, Path] = _paths()
ROOT: Path = P["ROOT"]
# -------------------------------------

def ensure_dirs() -> None:
    _ensure_dirs()

def env_presence(keys=("OPENAI_API_KEY","NOTION_TOKEN","SLACK_BOT_TOKEN")) -> Dict[str, str]:
    return _env_presence(keys)

def memory_file_ready() -> bool:
    mm = P["LEARNING_MEMORY"]
    if mm.exists():
        return True
    try:
        mm.write_text(json.dumps({"meta":{"created_by":"report_paths.py","version":1},"records":[]}, ensure_ascii=False), encoding="utf-8")
        return True
    except Exception:
        return False

if __name__ == "__main__":
    ensure_dirs()
    ok = memory_file_ready()
    print("VELOS_ROOT=", ROOT)
    print("learning_memory.json=", "ok" if ok else "failed")
    print("env=", env_presence())