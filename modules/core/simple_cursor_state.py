# VELOS 운영 철학 선언문
# - 파일명/경로 불변 · 거짓 코드 금지 · 자가 검증 필수 · 결과는 로그로 증빙

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict

ROOT = Path(r"C:\giwanos")
STATE_PATH = ROOT / "data" / "memory" / "runtime_state.json"


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    # 파일 락 메커니즘 추가
    lock = path.with_suffix(".lock")
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
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
    finally:
        try:
            os.remove(lock)
        except FileNotFoundError:
            pass


def get_cursor_in_use() -> bool:
    # 1) 환경변수 우선
    env = os.getenv("CURSOR_IN_USE")
    if env is not None:
        return env == "1"
    # 2) 파일 후순위
    d = _read_json(STATE_PATH)
    val = d.get("cursor_in_use")
    return bool(val) if val is not None else False


def set_cursor_in_use(flag: bool, source: str = "manual") -> None:
    d = _read_json(STATE_PATH)
    d["cursor_in_use"] = bool(flag)
    d["source"] = source
    d["last_update_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _write_json(STATE_PATH, d)
    # 환경변수도 동기화
    os.environ["CURSOR_IN_USE"] = "1" if flag else "0"
    os.environ["VELOS_SESSION_SOURCE"] = source


def get_runtime_state() -> Dict[str, Any]:
    d = _read_json(STATE_PATH)
    d.setdefault("cursor_in_use", get_cursor_in_use())
    d.setdefault("source", os.getenv("VELOS_SESSION_SOURCE") or d.get("source") or "unknown")
    return d


if __name__ == "__main__":
    # 자가 검증 테스트
    print("=== Simple Cursor State 자가 검증 테스트 ===")

    # 1. 초기 상태 확인
    print("1. 초기 상태:")
    initial_state = get_cursor_in_use()
    print(f"   cursor_in_use: {initial_state}")

    # 2. 상태 설정 테스트
    print("\n2. 상태 설정 테스트:")
    set_cursor_in_use(True, "test_simple")
    after_set = get_cursor_in_use()
    print(f"   설정 후: {after_set}")

    # 3. 환경변수 확인
    print(f"\n3. 환경변수 확인:")
    print(f"   CURSOR_IN_USE: {os.getenv('CURSOR_IN_USE')}")
    print(f"   VELOS_SESSION_SOURCE: {os.getenv('VELOS_SESSION_SOURCE')}")

    # 4. 런타임 상태 조회
    print("\n4. 런타임 상태 조회:")
    runtime_state = get_runtime_state()
    print(f"   런타임 상태: {runtime_state}")

    # 5. 상태 초기화
    print("\n5. 상태 초기화:")
    set_cursor_in_use(False, "test_complete")
    final_state = get_cursor_in_use()
    print(f"   최종 상태: {final_state}")

    print("\n=== 자가 검증 완료 ===")
