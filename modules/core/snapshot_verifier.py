#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VELOS Snapshot Verifier Module
스냅샷 파일들의 무결성을 검증하는 시스템입니다.
"""

import os
import sys
import json
import time
import hashlib
from typing import Dict, Any, List

# VELOS 운영 철학 선언문
# - 파일명 절대 변경 금지
# - 거짓코드 절대 금지
# - 모든 결과는 자가 검증 후 저장

ROOT = os.getenv("VELOS_ROOT", "/workspace")
SNAP_DIR = os.path.join(ROOT, "data", "snapshots")
CATALOG = os.path.join(SNAP_DIR, "checksums.json")
HEALTH = os.path.join(ROOT, "data", "logs", "system_health.json")


def sha256_hash(file_path: str, buffer_size: int = 1024 * 1024) -> str:
    """
    파일의 SHA256 해시를 계산합니다.

    Args:
        file_path: 해시를 계산할 파일 경로
        buffer_size: 읽기 버퍼 크기 (기본값: 1MB)

    Returns:
        str: SHA256 해시값 (hexdigest)
    """
    try:
        hash_obj = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(buffer_size)
                if not chunk:
                    break
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        print(f"[VELOS] SHA256 calculation failed for {file_path}: {e}")
        raise


def load_json(file_path: str) -> Dict[str, Any]:
    """
    JSON 파일을 안전하게 로드합니다.

    Args:
        file_path: 로드할 JSON 파일 경로

    Returns:
        Dict[str, Any]: 로드된 JSON 데이터 (실패 시 빈 딕셔너리)
    """
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception as e:
        print(f"[VELOS] Failed to load JSON from {file_path}: {e}")
        return {}


def save_json(file_path: str, data: Dict[str, Any]) -> None:
    """
    JSON 파일을 안전하게 저장합니다.

    Args:
        file_path: 저장할 JSON 파일 경로
        data: 저장할 데이터
    """
    try:
        # 디렉토리 생성
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # 임시 파일에 저장 후 원자적 교체
        tmp_path = file_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        os.replace(tmp_path, file_path)

    except Exception as e:
        print(f"[VELOS] Failed to save JSON to {file_path}: {e}")
        raise


def verify_snapshots(max_check: int = 50) -> Dict[str, Any]:
    """
    스냅샷 파일들의 무결성을 검증합니다.

    Args:
        max_check: 검증할 최대 파일 수 (최신 파일부터)

    Returns:
        Dict[str, Any]: 검증 결과
    """
    try:
        # 카탈로그 로드
        catalog = load_json(CATALOG)
        if not catalog:
            return {
                "success": False,
                "error": "Catalog not found or empty"
            }

        # ZIP 파일 목록 조회 (최신 파일부터)
        zip_files = [f for f in os.listdir(SNAP_DIR) if f.lower().endswith(".zip")]
        zip_files.sort(reverse=True)  # 최신 파일부터 정렬
        zip_files = zip_files[:max_check]  # 최대 검증 수 제한

        print(f"[VELOS] Verifying {len(zip_files)} snapshot files (max: {max_check})...")

        mismatches = []
        missing = []
        checked = 0
        verified_files = []

        for filename in zip_files:
            file_path = os.path.join(SNAP_DIR, filename)

            # 카탈로그에 없는 파일
            if filename not in catalog:
                missing.append({
                    "file": filename,
                    "reason": "not_in_catalog",
                    "file_path": file_path
                })
                print(f"   ❌ {filename}: Missing from catalog")
                continue

            try:
                # 현재 해시 계산
                current_sha256 = sha256_hash(file_path)
                expected_sha256 = catalog[filename]["sha256"]

                checked += 1

                if current_sha256 == expected_sha256:
                    verified_files.append({
                        "file": filename,
                        "sha256": current_sha256,
                        "file_size": os.path.getsize(file_path)
                    })
                    print(f"   ✅ {filename}: Verified")
                else:
                    mismatches.append({
                        "file": filename,
                        "expected": expected_sha256,
                        "actual": current_sha256,
                        "file_path": file_path,
                        "catalog_entry": catalog[filename]
                    })
                    print(f"   ❌ {filename}: Hash mismatch")
                    print(f"      Expected: {expected_sha256[:16]}...")
                    print(f"      Actual:   {current_sha256[:16]}...")

            except Exception as e:
                missing.append({
                    "file": filename,
                    "reason": f"verification_error: {str(e)}",
                    "file_path": file_path
                })
                print(f"   ❌ {filename}: Verification error - {e}")
                continue

        # 헬스 로그 업데이트
        health_data = load_json(HEALTH)
        health_data["snapshot_verify_last_ts"] = int(time.time())
        health_data["snapshot_verify_checked"] = checked
        health_data["snapshot_verify_mismatches"] = mismatches
        health_data["snapshot_verify_missing"] = missing
        health_data["snapshot_verify_ok"] = (len(mismatches) == 0 and len(missing) == 0)
        health_data["snapshot_verify_total_files"] = len(zip_files)
        health_data["snapshot_verify_verified_files"] = len(verified_files)
        save_json(HEALTH, health_data)

        return {
            "success": True,
            "checked": checked,
            "total_files": len(zip_files),
            "verified_files": len(verified_files),
            "mismatches": mismatches,
            "missing": missing,
            "integrity_ok": (len(mismatches) == 0 and len(missing) == 0),
            "verification_ts": int(time.time())
        }

    except Exception as e:
        print(f"[VELOS] Snapshot verification failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def get_verification_status() -> Dict[str, Any]:
    """
    최근 검증 상태를 조회합니다.

    Returns:
        Dict[str, Any]: 검증 상태 정보
    """
    try:
        health_data = load_json(HEALTH)

        return {
            "last_verification_ts": health_data.get("snapshot_verify_last_ts"),
            "checked_count": health_data.get("snapshot_verify_checked"),
            "total_files": health_data.get("snapshot_verify_total_files"),
            "verified_files": health_data.get("snapshot_verify_verified_files"),
            "mismatches_count": len(health_data.get("snapshot_verify_mismatches", [])),
            "missing_count": len(health_data.get("snapshot_verify_missing", [])),
            "integrity_ok": health_data.get("snapshot_verify_ok", False),
            "mismatches": health_data.get("snapshot_verify_mismatches", []),
            "missing": health_data.get("snapshot_verify_missing", [])
        }

    except Exception as e:
        return {
            "error": str(e)
        }


def main(max_check: int = 50) -> int:
    """
    메인 함수

    Args:
        max_check: 검증할 최대 파일 수

    Returns:
        int: 종료 코드 (0: 성공, 2: 경고/불일치)
    """
    try:
        print("=== VELOS Snapshot Integrity Verifier ===")

        result = verify_snapshots(max_check)

        if not result["success"]:
            print(f"❌ Verification failed: {result['error']}")
            return 1

        # 결과 출력
        print(f"\n=== Verification Summary ===")
        print(f"   Checked: {result['checked']}")
        print(f"   Total files: {result['total_files']}")
        print(f"   Verified: {result['verified_files']}")
        print(f"   Mismatches: {len(result['mismatches'])}")
        print(f"   Missing: {len(result['missing'])}")
        print(f"   Integrity OK: {result['integrity_ok']}")

        # Exit code 정책: 불일치나 누락 있으면 2(경고), 없으면 0
        if result['mismatches'] or result['missing']:
            print(f"\n[verify] mismatches={len(result['mismatches'])} missing={len(result['missing'])}")
            return 2

        print(f"\n[verify] ok, checked={result['checked']}")
        return 0

    except Exception as e:
        print(f"[VELOS] Main execution failed: {e}")
        return 1


if __name__ == "__main__":
    # 명령행 인수 파싱
    max_check = 50
    for i, arg in enumerate(sys.argv):
        if arg == "--max" and i + 1 < len(sys.argv):
            try:
                max_check = int(sys.argv[i + 1])
            except ValueError:
                print(f"[ERROR] Invalid max value: {sys.argv[i + 1]}")
                sys.exit(1)

    sys.exit(main(max_check))
