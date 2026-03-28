#!/usr/bin/env python3
import argparse, os, time, sys
from pathlib import Path
# Ensure project root on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from modules.core.path_manager import get_data_path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--days', type=int, default=30)
    args = ap.parse_args()
    snaps = get_data_path('snapshots')
    if not os.path.isdir(snaps):
        print('[cleanup_snapshots] no snapshots dir, skip')
        return 0
    now = time.time()
    cutoff = now - args.days*86400
    removed = 0
    for name in os.listdir(snaps):
        path = os.path.join(snaps, name)
        try:
            if os.path.isfile(path) and os.path.getmtime(path) < cutoff:
                os.remove(path)
                removed += 1
        except Exception:
            pass
    print(f'[cleanup_snapshots] removed={removed}, days>{args.days}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
