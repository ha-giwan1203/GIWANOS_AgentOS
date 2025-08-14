# VELOS 운영 철학 선언문
from __future__ import annotations
import json
from modules.velos_common import paths, ensure_dirs, env_presence

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


# --- BACKWARD COMPAT SHIM (VELOS) ---
# 기존 코드 호환: run_giwanos_master_loop.py 등에서 기대하는 ROOT, P 제공
try:
    from modules.velos_common import paths as _velos_paths
    _P = _velos_paths()
    ROOT = _P["ROOT"]
    P = _P  # dict-like: ROOT/DATA/REPORTS/AUTO/DISPATCH/LOGS/MEMORY/...
except Exception as _e:
    # 최후의 안전장치
    import os
    from pathlib import Path
    ROOT = Path(os.getenv("VELOS_ROOT", r"C:\giwanos")).resolve()
    P = {"ROOT": ROOT}
# --- END SHIM ---