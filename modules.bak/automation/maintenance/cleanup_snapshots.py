#!config.PROJECT_HOMEbin/env python3
from modules.core import config
"""
cleanup_snapshots.py   (modules/automation/maintenance/cleanup_snapshots.py)

Deletes incremental snapshot folders/files older than a retention period
(default 30 days) to save disk space.

Usage (repo root):
    python modules/automation/maintenance/cleanup_snapshots.py
    python modules/automation/maintenance/cleanup_snapshots.py --days 14
"""

import argparse
import datetime as dt
from pathlib import Path
import shutil
import sys

# <repo root>/modules/automation/maintenance/cleanup_snapshots.py
# parents[3] == repo root
SNAP_DIR = Path(__file__).resolve().parents[3] / "data" / "snapshots"


def cleanup(days: int):
    cutoff = dt.datetime.utcnow() - dt.timedelta(days=days)
    removed = []
    for child in SNAP_DIR.iterdir():
        try:
            mtime = dt.datetime.utcfromtimestamp(child.stat().st_mtime)
        except FileNotFoundError:
            continue
        if mtime < cutoff:
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)
            removed.append(child.name)
    return removed


def main():
    ap = argparse.ArgumentParser(description="Clean old snapshot artefacts.")
    ap.add_argument("--days", type=int, default=30, help="Retention period in days")
    args = ap.parse_args()

    if not SNAP_DIR.exists():
        print(f"{SNAP_DIR} not found", file=sys.stderr)
        sys.exit(1)

    removed = cleanup(args.days)
    print(f"Removed {len(removed)} snapshot item(s).")
    for name in removed:
        print(f"  - {name}")


if __name__ == "__main__":
    main()



