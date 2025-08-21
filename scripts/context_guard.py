# [ACTIVE] VELOS 운영 철학 선언문: 파일명 고정, 자가 검증 필수, 결과 기록, 경로/구조 불변, 실패 시 안전 복구와 알림.
import json
import os
import sys
import time

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


ROOT = get_velos_root() if "get_velos_root" in locals() else "/home/user/webapp"
HEALTH = os.path.join(ROOT, "data", "logs", "system_health.json")

# 임계값(분): 환경변수로 오버라이드 가능
FLUSH_MAX_AGE_MIN = int(os.getenv("VELOS_FLUSH_MAX_AGE_MIN", "15"))
CTX_MAX_AGE_MIN = int(os.getenv("VELOS_CTX_MAX_AGE_MIN", "15"))


def jload(p):
    try:
        with open(p, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return {}


def alert(title: str, message: str):
    # 가능하면 내부 알림 모듈 사용, 실패해도 가드가 죽진 않게 설계
    try:
        sys.path.append(ROOT)
        from tools.notifications.system_alert_notifier import send_alert  # 구현돼 있음

        send_alert(title=title, message=message)
    except Exception:
        print(f"[ALERT-FALLBACK] {title}: {message}")


def mins_ago(ts: int) -> int:
    return int((time.time() - int(ts)) / 60)


def main():
    h = jload(HEALTH)
    last_flush_ts = int(h.get("last_flush_ts", 0))
    last_ctx_ts = int(h.get("context_build_last_ts", 0))

    flush_age = mins_ago(last_flush_ts) if last_flush_ts else 9999
    ctx_age = mins_ago(last_ctx_ts) if last_ctx_ts else 9999

    bad = []
    if flush_age > FLUSH_MAX_AGE_MIN:
        bad.append(f"flush_age={flush_age}m > {FLUSH_MAX_AGE_MIN}m")
    if ctx_age > CTX_MAX_AGE_MIN:
        bad.append(f"context_age={ctx_age}m > {CTX_MAX_AGE_MIN}m")

    status = {
        "flush_age_min": flush_age,
        "context_age_min": ctx_age,
        "flush_ok": flush_age <= FLUSH_MAX_AGE_MIN,
        "context_ok": ctx_age <= CTX_MAX_AGE_MIN,
        "checked_ts": int(time.time()),
    }
    print(json.dumps(status, ensure_ascii=False, indent=2))

    if bad:
        alert(
            title="VELOS Context/Flush Stale",
            message="; ".join(bad) + " (check run_giwanos_master_loop / memory_adapter)",
        )
        sys.exit(2)  # 스케줄러가 실패로 기록하게


if __name__ == "__main__":
    main()
