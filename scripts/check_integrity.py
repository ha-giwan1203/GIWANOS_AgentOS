#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Path manager imports (Phase 2 standardization)
try:
    from modules.core.path_manager import (
        get_config_path,
        get_data_path,
        get_db_path,
        get_velos_root,
    )
except ImportError:
    # Fallback functions for backward compatibility
    def get_velos_root():
        return "C:\giwanos"

    def get_data_path(*parts):
        return os.path.join("C:\giwanos", "data", *parts)

    def get_config_path(*parts):
        return os.path.join("C:\giwanos", "configs", *parts)

    def get_db_path():
        return "C:\giwanos/data/memory/velos.db"


"""
VELOS Integrity Check Script
헬스 로그에서 무결성 정보를 확인합니다.
"""

import json
import os

ROOT = get_velos_root() if "get_velos_root" in locals() else "C:\giwanos"
HEALTH = os.path.join(ROOT, "data", "logs", "system_health.json")


def main():
    try:
        if not os.path.exists(HEALTH):
            print("[ERROR] Health log not found")
            return

        with open(HEALTH, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        print("=== VELOS Integrity Info ===")
        print(f"snapshot_last_sha256: {data.get('snapshot_last_sha256')}")
        print(f"snapshot_last_file: {data.get('snapshot_last_file')}")
        print(f"snapshot_last_ts: {data.get('snapshot_last_ts')}")
        print(f"snapshot_last_size: {data.get('snapshot_last_size')}")
        print(f"snapshot_integrity_ok: {data.get('snapshot_integrity_ok')}")
        print(f"snapshot_integrity_last_check: {data.get('snapshot_integrity_last_check')}")

    except Exception as e:
        print(f"[ERROR] Failed to check integrity: {e}")


if __name__ == "__main__":
    main()
