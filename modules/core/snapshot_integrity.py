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
        return "/home/user/webapp"

    def get_data_path(*parts):
        return os.path.join("/home/user/webapp", "data", *parts)

    def get_config_path(*parts):
        return os.path.join("/home/user/webapp", "configs", *parts)

    def get_db_path():
        return "/home/user/webapp/data/memory/velos.db"


"""
VELOS Snapshot Integrity Module
스냅샷 파일의 SHA256 무결성 해시를 계산하고 헬스 로그에 기록합니다.
"""

import hashlib
import json
import os
import time
from typing import Any, Dict

# VELOS 운영 철학 선언문
# - 파일명 절대 변경 금지
# - 거짓코드 절대 금지
# - 모든 결과는 자가 검증 후 저장

ROOT = get_velos_root() if "get_velos_root" in locals() else "/home/user/webapp"
HEALTH = os.path.join(ROOT, "data", "logs", "system_health.json")


def sha256_hash(file_path: str, buffer_size: int = 1024 * 1024) -> str:
    """
    파일의 SHA256 해시를 계산합니다.

    Args:
        file_path: 해시를 계산할 파일 경로
        buffer_size: 읽기 버퍼 크기 (기본값: 1MB)

    Returns:
        str: SHA256 해시값 (hexdigest)

    Raises:
        FileNotFoundError: 파일이 존재하지 않는 경우
        OSError: 파일 읽기 오류
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        hash_obj = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(buffer_size)
                if not chunk:
                    break
                hash_obj.update(chunk)

        return hash_obj.hexdigest()

    except Exception as e:
        print(f"[VELOS] SHA256 calculation failed: {e}")
        raise


def record_snapshot_integrity(snapshot_path: str) -> Dict[str, Any]:
    """
    스냅샷 파일의 무결성을 기록합니다.

    Args:
        snapshot_path: 스냅샷 파일 경로

    Returns:
        Dict[str, Any]: 기록된 메타데이터
    """
    try:
        # 1) SHA256 해시 계산
        print(f"[VELOS] Calculating SHA256 for: {os.path.basename(snapshot_path)}")
        digest = sha256_hash(snapshot_path)

        # 2) 메타데이터 구성
        meta = {
            "ts": int(time.time()),
            "snapshot": os.path.basename(snapshot_path),
            "sha256": digest,
            "file_size": os.path.getsize(snapshot_path),
            "file_path": snapshot_path,
        }

        print(f"[VELOS] snapshot.sha256: {digest}")
        print(f"[VELOS] snapshot.size: {meta['file_size']} bytes")

        # 3) 헬스 로그에 저장
        _save_integrity_to_health(meta)

        return meta

    except Exception as e:
        print(f"[VELOS] Snapshot integrity recording failed: {e}")
        return {
            "error": str(e),
            "ts": int(time.time()),
            "snapshot": os.path.basename(snapshot_path) if snapshot_path else "unknown",
        }


def _save_integrity_to_health(meta: Dict[str, Any]) -> None:
    """
    무결성 정보를 헬스 로그에 저장합니다.

    Args:
        meta: 저장할 메타데이터
    """
    try:
        # 헬스 로그 디렉토리 생성
        os.makedirs(os.path.dirname(HEALTH), exist_ok=True)

        # 기존 헬스 데이터 로드
        data = {}
        if os.path.exists(HEALTH):
            with open(HEALTH, "r", encoding="utf-8-sig") as f:
                data = json.load(f)

        # 무결성 정보 업데이트
        data["snapshot_last_sha256"] = meta["sha256"]
        data["snapshot_last_file"] = meta["snapshot"]
        data["snapshot_last_ts"] = meta["ts"]
        data["snapshot_last_size"] = meta.get("file_size", 0)
        data["snapshot_integrity_ok"] = True
        data["snapshot_integrity_last_check"] = meta["ts"]

        # 임시 파일에 저장 후 원자적 교체
        tmp_path = HEALTH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        os.replace(tmp_path, HEALTH)

        print(f"[VELOS] Integrity recorded to health log: {meta['sha256']}")

    except Exception as e:
        print(f"[WARN] Snapshot integrity write failed: {e}")


def verify_snapshot_integrity(snapshot_path: str, expected_sha256: str = None) -> Dict[str, Any]:
    """
    스냅샷 파일의 무결성을 검증합니다.

    Args:
        snapshot_path: 검증할 스냅샷 파일 경로
        expected_sha256: 예상 SHA256 해시값 (None이면 헬스 로그에서 조회)

    Returns:
        Dict[str, Any]: 검증 결과
    """
    try:
        # 1) 현재 해시 계산
        current_sha256 = sha256_hash(snapshot_path)

        # 2) 예상 해시 조회 (제공되지 않은 경우)
        if expected_sha256 is None:
            expected_sha256 = _get_expected_sha256(snapshot_path)

        # 3) 검증
        is_valid = current_sha256 == expected_sha256

        result = {
            "ts": int(time.time()),
            "snapshot": os.path.basename(snapshot_path),
            "current_sha256": current_sha256,
            "expected_sha256": expected_sha256,
            "integrity_ok": is_valid,
            "file_size": os.path.getsize(snapshot_path),
            "file_path": snapshot_path,
        }

        if is_valid:
            print(f"[VELOS] ✅ Snapshot integrity verified: {current_sha256}")
        else:
            print(f"[VELOS] ❌ Snapshot integrity failed:")
            print(f"   Expected: {expected_sha256}")
            print(f"   Current:  {current_sha256}")

        return result

    except Exception as e:
        print(f"[VELOS] Snapshot integrity verification failed: {e}")
        return {
            "error": str(e),
            "ts": int(time.time()),
            "snapshot": os.path.basename(snapshot_path) if snapshot_path else "unknown",
            "integrity_ok": False,
        }


def _get_expected_sha256(snapshot_path: str) -> str:
    """
    헬스 로그에서 예상 SHA256 해시값을 조회합니다.

    Args:
        snapshot_path: 스냅샷 파일 경로

    Returns:
        str: 예상 SHA256 해시값
    """
    try:
        if not os.path.exists(HEALTH):
            raise FileNotFoundError("Health log not found")

        with open(HEALTH, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        # 파일명이 일치하는지 확인
        expected_file = data.get("snapshot_last_file")
        if expected_file and expected_file == os.path.basename(snapshot_path):
            return data.get("snapshot_last_sha256", "")
        else:
            raise ValueError(
                f"Snapshot file mismatch: expected {expected_file}, got {os.path.basename(snapshot_path)}"
            )

    except Exception as e:
        print(f"[VELOS] Failed to get expected SHA256: {e}")
        return ""


def get_integrity_status() -> Dict[str, Any]:
    """
    현재 무결성 상태를 조회합니다.

    Returns:
        Dict[str, Any]: 무결성 상태 정보
    """
    try:
        if not os.path.exists(HEALTH):
            return {"error": "Health log not found"}

        with open(HEALTH, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        return {
            "snapshot_last_sha256": data.get("snapshot_last_sha256"),
            "snapshot_last_file": data.get("snapshot_last_file"),
            "snapshot_last_ts": data.get("snapshot_last_ts"),
            "snapshot_last_size": data.get("snapshot_last_size"),
            "snapshot_integrity_ok": data.get("snapshot_integrity_ok", False),
            "snapshot_integrity_last_check": data.get("snapshot_integrity_last_check"),
        }

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # 테스트 실행
    import sys

    if len(sys.argv) > 1:
        snapshot_path = sys.argv[1]
        print(f"=== VELOS Snapshot Integrity Test ===")
        print(f"Testing: {snapshot_path}")

        # 무결성 기록
        meta = record_snapshot_integrity(snapshot_path)
        print(f"Recorded: {meta}")

        # 무결성 검증
        result = verify_snapshot_integrity(snapshot_path)
        print(f"Verified: {result}")

        # 상태 조회
        status = get_integrity_status()
        print(f"Status: {status}")
    else:
        print("Usage: python snapshot_integrity.py <snapshot_path>")
