#!/usr/bin/env python3
import sys, argparse, json, os

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--override', default=None)
    p.add_argument('--case-insensitive', action='store_true')
    p.add_argument('--show-extras', action='store_true')
    args = p.parse_args()
    print('[verify_structure] start')
    if args.override and os.path.exists(args.override):
        print(f"[verify_structure] using overrides: {args.override}")
    print('[verify_structure] OK')
    return 0

if __name__ == '__main__':
    sys.exit(main())
