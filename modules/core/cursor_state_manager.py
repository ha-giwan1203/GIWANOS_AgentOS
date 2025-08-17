# =========================================================
# VELOS 운영 철학 선언문
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=C:/giwanos 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================

"""
VELOS Cursor State Manager

Cursor IDE의 사용 상태를 관리하고 TTL 기반 자동 만료를 처리합니다.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any

# VELOS 루트 경로
ROOT = Path("C:/giwanos")

# 추가: 상단 상수
SCHEMA_VERSION = 1
TTL_MINUTES = 30  # 세션 갱신 없으면 자동 false
ENV_STATE_PATH = os.getenv("VELOS_RUNTIME_STATE_PATH")

# 수정: STATE_PATH 결정
STATE_PATH = (
    Path(ENV_STATE_PATH)
    if ENV_STATE_PATH
    else ROOT / "data" / "memory" / "runtime_state.json"
)


def _read_json(path: str) -> Dict[str, Any]:
    """JSON 파일 안전 읽기"""
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_json(path: str, obj: Dict[str, Any]) -> None:
    """JSON 파일 안전 쓰기 (원자적 연산 + 파일 락)"""
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)

    lock = path_obj.with_suffix(".lock")
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
        tmp = path_obj.with_suffix(".tmp")
        tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path_obj)
    finally:
        try:
            os.remove(lock)
        except FileNotFoundError:
            pass


def _utc_now_iso() -> str:
    import time

    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _is_expired(last_iso: str | None) -> bool:
    if not last_iso:
        return True
    from datetime import datetime, timezone, timedelta

    try:
        ts = datetime.fromisoformat(last_iso.replace("Z", "+00:00"))
    except ValueError:
        return True
    return datetime.now(timezone.utc) - ts > timedelta(minutes=TTL_MINUTES)


def get_cursor_in_use() -> bool:
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


def set_cursor_in_use(flag: bool, source: str = "manual") -> None:
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


def reconcile_env_file_state() -> dict:
    d = _read_json(STATE_PATH)
    file_flag = bool(d.get("cursor_in_use", False))
    env_flag = os.getenv("CURSOR_IN_USE")
    env_flag = (env_flag == "1") if env_flag is not None else None

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


def get_cursor_state_info() -> Dict[str, Any]:
    """Cursor 상태 정보 조회"""
    d = _read_json(STATE_PATH)
    env_flag = os.getenv("CURSOR_IN_USE")
    env_flag = (env_flag == "1") if env_flag is not None else None

    return {
        "schema_version": d.get("schema_version", 0),
        "cursor_in_use": bool(d.get("cursor_in_use", False)),
        "env_cursor_in_use": env_flag,
        "source": d.get("source", "unknown"),
        "last_update_utc": d.get("last_update_utc"),
        "expired": _is_expired(d.get("last_update_utc")),
        "ttl_minutes": TTL_MINUTES,
        "state_path": str(STATE_PATH),
        "reconciled": reconcile_env_file_state(),
    }


def reset_cursor_state() -> None:
    """Cursor 상태 초기화"""
    set_cursor_in_use(False, source="reset")


if __name__ == "__main__":
    # 자가 검증 테스트
    print("=== VELOS Cursor State Manager 자가 검증 테스트 ===")

    # 1. 초기 상태 확인
    print("1. 초기 상태:")
    info = get_cursor_state_info()
    print(f"   cursor_in_use: {info['cursor_in_use']}")
    print(f"   env_cursor_in_use: {info['env_cursor_in_use']}")
    print(f"   expired: {info['expired']}")

    # 2. 상태 설정 테스트
    print("\n2. 상태 설정 테스트:")
    set_cursor_in_use(True, source="test")
    info = get_cursor_state_info()
    print(f"   cursor_in_use: {info['cursor_in_use']}")
    print(f"   source: {info['source']}")

    # 3. 환경변수 확인
    print(f"\n3. 환경변수 확인:")
    print(f"   CURSOR_IN_USE: {os.getenv('CURSOR_IN_USE')}")
    print(f"   VELOS_SESSION_SOURCE: {os.getenv('VELOS_SESSION_SOURCE')}")

    # 4. 상태 조정 테스트
    print("\n4. 상태 조정 테스트:")
    reconciled = reconcile_env_file_state()
    print(f"   file_flag: {reconciled['file_flag']}")
    print(f"   env_flag: {reconciled['env_flag']}")
    print(f"   final: {reconciled['final']}")

    # 5. 상태 초기화
    print("\n5. 상태 초기화:")
    reset_cursor_state()
    info = get_cursor_state_info()
    print(f"   cursor_in_use: {info['cursor_in_use']}")

    print("\n=== 자가 검증 완료 ===")
