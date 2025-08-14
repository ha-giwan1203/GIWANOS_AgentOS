# VELOS 운영 철학 선언문
from __future__ import annotations
import json
from velos_common import paths, ensure_dirs, env_presence

def memory_file_ready() -> bool:
    p = paths()
    mm = p["LEARNING_MEMORY"]
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
    p = paths()
    print("VELOS_ROOT=", p["ROOT"])
    print("learning_memory.json=", "ok" if ok else "failed")
    print("env=", env_presence())