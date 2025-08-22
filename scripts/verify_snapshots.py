#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VELOS Snapshot Verification Script
스냅샷 무결성을 검증하는 스크립트입니다.
"""

import sys
import os

# ROOT 경로 설정
ROOT = os.getenv("VELOS_ROOT", "/workspace")
if ROOT not in sys.path:
    sys.path.append(ROOT)

def main():
    try:
        from modules.core.snapshot_verifier import main as verifier_main

        print("=== VELOS Snapshot Verification Script ===")

        # --max 플래그 확인
        max_check = 50  # 기본값
        for i, arg in enumerate(sys.argv):
            if arg == "--max" and i + 1 < len(sys.argv):
                try:
                    max_check = int(sys.argv[i + 1])
                except ValueError:
                    print(f"[ERROR] Invalid max value: {sys.argv[i + 1]}")
                    return 1

        print(f"Running snapshot verification with max_check={max_check}")

        # 무결성 검증 실행
        exit_code = verifier_main(max_check)

        if exit_code == 0:
            print("✅ Snapshot verification completed successfully")
        elif exit_code == 2:
            print("⚠️ Snapshot verification completed with warnings (mismatches/missing)")
        else:
            print(f"❌ Snapshot verification failed with code: {exit_code}")

        return exit_code

    except Exception as e:
        print(f"[ERROR] Snapshot verification script failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
