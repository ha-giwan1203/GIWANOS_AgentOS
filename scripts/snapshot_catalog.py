#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VELOS Snapshot Catalog Script
스냅샷 카탈로그를 관리하는 스크립트입니다.
"""

import sys
import os

# ROOT 경로 설정
ROOT = os.getenv("VELOS_ROOT", "/workspace")
if ROOT not in sys.path:
    sys.path.append(ROOT)

def main():
    try:
        from modules.core.snapshot_catalog import main as catalog_main

        print("=== VELOS Snapshot Catalog Script ===")

        # --all 플래그 확인
        backfill_all = "--all" in sys.argv

        if backfill_all:
            print("Running catalog update with --all flag (backfill mode)")
        else:
            print("Running catalog update (incremental mode)")

        # 카탈로그 업데이트 실행
        exit_code = catalog_main(backfill_all)

        if exit_code == 0:
            print("✅ Snapshot catalog update completed successfully")
        else:
            print(f"❌ Snapshot catalog update failed with code: {exit_code}")

        return exit_code

    except Exception as e:
        print(f"[ERROR] Snapshot catalog script failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
