# VELOS 운영 철학 선언문
from __future__ import annotations
import os
from pathlib import Path
from typing import Dict

def velos_root() -> Path:
    return Path(os.getenv("VELOS_ROOT", r"C:\giwanos")).resolve()

def paths() -> Dict[str, Path]:
    root = velos_root()
    data = root / "data"
    p = {
        "ROOT": root,
        "DATA": data,
        "REPORTS": data / "reports",
        "AUTO": data / "reports" / "auto",
        "DISPATCH": data / "reports" / "_dispatch",
        "LOGS": data / "logs",
        "MEMORY": data / "memory",
    }
    p["LEARNING_MEMORY"] = p["MEMORY"] / "learning_memory.json"
    p["SELF_CHECK_SUMMARY"] = p["AUTO"] / "self_check_summary.txt"
    p["AUTOFIX_LOG"] = p["LOGS"] / "autofix.log"
    return p

def ensure_dirs():
    for d in [*paths().values()]:
        if d.suffix:  # skip files
            continue
        d.mkdir(parents=True, exist_ok=True)

def env_presence(keys=("OPENAI_API_KEY","NOTION_TOKEN","SLACK_BOT_TOKEN")) -> Dict[str, str]:
    return {k: ("present" if os.getenv(k) else "missing") for k in keys}
