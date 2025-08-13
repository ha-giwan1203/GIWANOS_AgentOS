from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

GIWANOS = Path(r"C:\giwanos")
LOGS = GIWANOS / "data" / "logs"
SNAP = GIWANOS / "data" / "snapshots"


def has_giwanos_path() -> bool:
    env_ok = "giwanos" in (os.environ.get("PYTHONPATH", "") or "")
    path_ok = any(p.replace("\\", "/").rstrip("/").lower().endswith("/giwanos") for p in sys.path)
    spec_ok = importlib.util.find_spec("app") is not None
    return env_ok or path_ok or spec_ok


def do_precheck():
    data = {
        "root_exists": GIWANOS.exists(),
        "logs_exists": LOGS.exists(),
        "snapshots_exists": SNAP.exists(),
        "pythonpath_contains_giwanos": has_giwanos_path(),
        "missing": [],
    }
    print(json.dumps(data, ensure_ascii=False, indent=2))


def do_make_report():
    py = r"C:\Users\User\venvs\velos\Scripts\python.exe"
    rep = subprocess.check_output(
        [py, str(GIWANOS / "scripts" / "velos_report.py")], text=True
    ).strip()
    print(f"[REPORT] {rep}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--precheck", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--make-report", action="store_true")
    args = ap.parse_args(argv)

    if args.precheck:
        do_precheck()
        return 0
    if args.dry_run:
        print("[DRY-RUN] VELOS master loop would execute tasks here.")
        return 0
    if args.make_report:
        do_make_report()
        return 0

    print("[INFO] No-op. Use --precheck or --dry-run or --make-report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
