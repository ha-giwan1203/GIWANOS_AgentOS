#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VELOS Snapshot Catalog Module
스냅샷 파일들의 체크섬을 관리하는 카탈로그 시스템입니다.
"""

import hashlib
import json
import os
import sys
import time
from typing import Any, Dict, List

# VELOS 운영 철학 선언문
# - 파일명 절대 변경 금지
# - 거짓코드 절대 금지
# - 모든 결과는 자가 검증 후 저장

ROOT = r"C:\giwanos"
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


def update_snapshot_catalog(backfill_all: bool = False) -> Dict[str, Any]:
    """
    스냅샷 카탈로그를 업데이트합니다.

    Args:
        backfill_all: 모든 파일을 다시 처리할지 여부

    Returns:
        Dict[str, Any]: 업데이트 결과
    """
    try:
        # 스냅샷 디렉토리 생성
        os.makedirs(SNAP_DIR, exist_ok=True)

        # 기존 카탈로그 로드
        catalog = load_json(CATALOG)

        # ZIP 파일 목록 조회
        zip_files = [f for f in os.listdir(SNAP_DIR) if f.lower().endswith(".zip")]
        zip_files.sort()  # 시간순 정렬

        updated_count = 0
        processed_files = []

        print(f"[VELOS] Processing {len(zip_files)} snapshot files...")

        for filename in zip_files:
            file_path = os.path.join(SNAP_DIR, filename)

            # 백필 모드이거나 카탈로그에 없는 파일인 경우 처리
            if backfill_all or filename not in catalog:
                try:
                    print(f"[VELOS] Calculating SHA256 for: {filename}")
                    digest = sha256_hash(file_path)
                    file_size = os.path.getsize(file_path)

                    catalog[filename] = {
                        "sha256": digest,
                        "recorded_ts": int(time.time()),
                        "file_size": file_size,
                        "file_path": file_path,
                    }

                    updated_count += 1
                    processed_files.append(
                        {"filename": filename, "sha256": digest, "file_size": file_size}
                    )

                    print(f"   ✅ {filename}: {digest[:16]}... ({file_size} bytes)")

                except Exception as e:
                    print(f"   ❌ {filename}: {e}")
                    continue

        # 카탈로그 저장
        if updated_count > 0:
            save_json(CATALOG, catalog)
            print(f"[VELOS] Catalog updated: {updated_count} files processed")

        # 헬스 로그 업데이트
        health_data = load_json(HEALTH)
        health_data["snapshot_catalog_last_update"] = int(time.time())
        health_data["snapshot_catalog_entries"] = len(catalog)
        health_data["snapshot_catalog_total_files"] = len(zip_files)
        health_data["snapshot_catalog_updated_count"] = updated_count
        save_json(HEALTH, health_data)

        return {
            "success": True,
            "catalog_entries": len(catalog),
            "total_files": len(zip_files),
            "updated_count": updated_count,
            "processed_files": processed_files,
            "catalog_path": CATALOG,
        }

    except Exception as e:
        print(f"[VELOS] Catalog update failed: {e}")
        return {"success": False, "error": str(e)}


def verify_snapshot_integrity(filename: str) -> Dict[str, Any]:
    """
    특정 스냅샷 파일의 무결성을 검증합니다.

    Args:
        filename: 검증할 스냅샷 파일명

    Returns:
        Dict[str, Any]: 검증 결과
    """
    try:
        catalog = load_json(CATALOG)

        if filename not in catalog:
            return {"success": False, "error": f"File {filename} not found in catalog"}

        file_path = os.path.join(SNAP_DIR, filename)
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File {filename} not found on disk"}

        # 현재 해시 계산
        current_sha256 = sha256_hash(file_path)
        expected_sha256 = catalog[filename]["sha256"]

        is_valid = current_sha256 == expected_sha256

        return {
            "success": True,
            "filename": filename,
            "current_sha256": current_sha256,
            "expected_sha256": expected_sha256,
            "integrity_ok": is_valid,
            "file_size": os.path.getsize(file_path),
            "catalog_entry": catalog[filename],
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def get_catalog_status() -> Dict[str, Any]:
    """
    카탈로그 상태를 조회합니다.

    Returns:
        Dict[str, Any]: 카탈로그 상태 정보
    """
    try:
        catalog = load_json(CATALOG)
        health_data = load_json(HEALTH)

        zip_files = [f for f in os.listdir(SNAP_DIR) if f.lower().endswith(".zip")]

        return {
            "catalog_entries": len(catalog),
            "total_files": len(zip_files),
            "last_update": health_data.get("snapshot_catalog_last_update"),
            "catalog_path": CATALOG,
            "snapshot_dir": SNAP_DIR,
            "files_in_catalog": list(catalog.keys()),
            "files_on_disk": zip_files,
        }

    except Exception as e:
        return {"error": str(e)}


def main(backfill_all: bool = False) -> int:
    """
    메인 함수

    Args:
        backfill_all: 모든 파일을 다시 처리할지 여부

    Returns:
        int: 종료 코드 (0: 성공, 1: 실패)
    """
    try:
        print("=== VELOS Snapshot Catalog Manager ===")

        result = update_snapshot_catalog(backfill_all)

        if result["success"]:
            print(f"✅ Catalog update completed")
            print(f"   Entries: {result['catalog_entries']}")
            print(f"   Total files: {result['total_files']}")
            print(f"   Updated: {result['updated_count']}")
            print(f"   Catalog: {result['catalog_path']}")

            # 결과를 JSON으로 출력
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        else:
            print(f"❌ Catalog update failed: {result['error']}")
            return 1

    except Exception as e:
        print(f"[VELOS] Main execution failed: {e}")
        return 1


if __name__ == "__main__":
    backfill_all = "--all" in sys.argv
    sys.exit(main(backfill_all))
