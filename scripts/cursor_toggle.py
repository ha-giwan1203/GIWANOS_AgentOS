#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VELOS Cursor State Toggle Script

Cursor 상태를 켜고 끄는 간단한 스크립트입니다.
"""

import os
import sys
import json
import time
from pathlib import Path

# ROOT 경로 설정
ROOT = Path("C:/giwanos")

# 상수 정의
SCHEMA_VERSION = 1
TTL_MINUTES = 30  # 세션 갱신 없으면 자동 false
ENV_STATE_PATH = os.getenv("VELOS_RUNTIME_STATE_PATH")

# STATE_PATH 결정
DEFAULT_STATE_PATH = ROOT / "data" / "memory" / "runtime_state.json"
STATE_PATH = Path(ENV_STATE_PATH) if ENV_STATE_PATH else DEFAULT_STATE_PATH


def _read_json(path: Path) -> dict:
    """JSON 파일 읽기"""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _utc_now_iso() -> str:
    """현재 UTC 시간을 ISO 형식으로 반환"""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _is_expired(last_iso: str | None) -> bool:
    """TTL 만료 여부 확인"""
    if not last_iso:
        return True
    from datetime import datetime, timezone, timedelta

    try:
        ts = datetime.fromisoformat(last_iso.replace("Z", "+00:00"))
    except ValueError:
        return True
    return datetime.now(timezone.utc) - ts > timedelta(minutes=TTL_MINUTES)


def _write_json(path: Path, data: dict) -> None:
    """JSON 파일 쓰기 (파일 락 + 권한 문제 우회)"""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_suffix(".lock")
    # 가난하지만 단순한 락: 독점 생성 시도
    import time

    for _ in range(50):
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            time.sleep(0.05)
    else:
        raise RuntimeError(f"파일 락 획득 실패: {lock}")

    try:
        tmp = path.with_suffix(".tmp")
        content = json.dumps(data, ensure_ascii=False, indent=2)
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(path)
    except PermissionError:
        # 권한 문제 시 환경변수만 설정
        print("[WARNING] 파일 쓰기 권한 없음, 환경변수만 설정")
    finally:
        try:
            os.remove(lock)
        except FileNotFoundError:
            pass


def set_cursor_in_use(flag: bool, source: str = "manual") -> None:
    """Cursor 상태 설정"""
    d = _read_json(STATE_PATH)
    d.update(
        {
            "schema_version": SCHEMA_VERSION,
            "cursor_in_use": bool(flag),
            "source": source,
            "last_update_utc": _utc_now_iso(),
        }
    )
    _write_json(STATE_PATH, d)
    os.environ["CURSOR_IN_USE"] = "1" if flag else "0"
    os.environ["VELOS_SESSION_SOURCE"] = source


def get_cursor_in_use() -> bool:
    """Cursor 상태 확인"""
    # ENV 우선
    env = os.getenv("CURSOR_IN_USE")
    if env is not None:
        return env == "1"
    # 파일 폴백 + TTL
    d = _read_json(STATE_PATH)
    flag = bool(d.get("cursor_in_use", False))
    if _is_expired(d.get("last_update_utc")):
        # 만료면 프로세스 보정 체크(있으면 true 승격)
        try:
            import psutil

            has_cursor = any(
                "cursor" in (p.name() or "").lower()
                for p in psutil.process_iter(["name"])
            )
        except Exception:
            has_cursor = False
        return bool(has_cursor and flag)
    return flag


def reconcile_env_file_state() -> dict:
    """환경변수와 파일 상태를 조정"""
    d = _read_json(STATE_PATH)
    file_flag = bool(d.get("cursor_in_use", False))
    env_flag = os.getenv("CURSOR_IN_USE")
    env_flag = (env_flag is not None) and (env_flag == "1")

    # 파일 우선
    final = file_flag
    if env_flag is None or env_flag != file_flag:
        os.environ["CURSOR_IN_USE"] = "1" if file_flag else "0"

    # TTL 만료면 false, 단 실제 커서 프로세스 있으면 true로 승격
    expired = _is_expired(d.get("last_update_utc"))
    if expired:
        try:
            import psutil

            has_cursor = any(
                "cursor" in (p.name() or "").lower()
                for p in psutil.process_iter(["name"])
            )
        except Exception:
            has_cursor = False
        if not has_cursor:
            final = False
            set_cursor_in_use(False, source="auto_expired")

    return {
        "file_flag": file_flag,
        "env_flag": env_flag,
        "expired": expired,
        "final": bool(final),
    }


def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("사용법: python cursor_toggle.py [on|off] [source]")
        print("  on: Cursor 상태 켜기")
        print("  off: Cursor 상태 끄기")
        print("  source: 상태 변경 소스 (기본값: manual)")
        return

    action = sys.argv[1].lower()
    source = sys.argv[2] if len(sys.argv) > 2 else "manual"

    if action == "on":
        set_cursor_in_use(True, source)
        print("cursor_in_use=True")
    elif action == "off":
        set_cursor_in_use(False, source)
        print("cursor_in_use=False")
    else:
        print(f"알 수 없는 액션: {action}")
        return

    # 현재 상태 확인
    current_state = get_cursor_in_use()
    print(f"현재 상태: {current_state}")


if __name__ == "__main__":
    main()
