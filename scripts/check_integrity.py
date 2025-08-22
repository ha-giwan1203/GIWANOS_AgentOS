#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VELOS Integrity Check Script
헬스 로그에서 무결성 정보를 확인합니다.
"""

import json
import os

# ROOT 경로 설정
ROOT = os.getenv("VELOS_ROOT", "/workspace")
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
