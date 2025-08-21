# -*- coding: utf-8 -*-
"""
VELOS: Single Python Master Loop
- Windows Task Scheduler는 5분마다 이 파일만 실행
- 모든 잡(Daily/Weekly/Hourly)은 내부 디스패처가 판단해 실행
- 설정:   C:\giwanos\data\jobs.json         (잡 정의)
- 상태:   C:\giwanos\data\job_state.json    (마지막 실행 시각)
- 로그:   C:\giwanos\data\logs\jobs.log
옵션:
  --list                 등록된 잡 목록 출력
  --force JOBNAME        특정 잡 강제 실행
  --now YYYY-MM-DDTHH:MM 테스트용 현재시각 주입(로컬시간)
"""

import atexit
import datetime as _dt
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# ------------------- 경로/파일 -------------------
ROOT = Path(os.environ.get("VELOS_ROOT", r"C:\giwanos"))
DATA = ROOT / "data"
LOGD = DATA / "logs"
LOGD.mkdir(parents=True, exist_ok=True)

JOBS_FILE = DATA / "jobs.json"
STATE_FILE = DATA / "job_state.json"
RUN_LOG = LOGD / "jobs.log"
LOCK_FILE = DATA / ".velos.py.lock"


# ------------------- 싱글톤 락 -------------------
def acquire_lock():
    """Python 레벨 싱글톤 락 획득"""
    try:
        # O_EXCL: 이미 있으면 실패. 윈도우에서도 동작.
        fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)

        def _cleanup():
            try:
                os.remove(LOCK_FILE)
            except OSError:
                pass

        atexit.register(_cleanup)
        return True
    except FileExistsError:
        return False


# ------------------- 유틸 -------------------
def _log(msg: str):
    ts = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(RUN_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


def _load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except Exception as e:
        _log(f"[WARN] load_json({path}) -> {e}")
        return default


def _save_json(path: str, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _ensure_default_jobs():
    if not os.path.exists(JOBS_FILE):
        default_jobs = [
            {"name": "DailyReport", "interval": "daily", "time": "09:05"},
            {"name": "WeeklyAudit", "interval": "weekly", "day": "monday", "time": "09:30"},
            {"name": "HealthCheck", "interval": "hourly", "minute": 0},
        ]
        _save_json(JOBS_FILE, default_jobs)
        _log("jobs.json created with defaults")


def _parse_hhmm(s: str):
    hh, mm = s.split(":")
    return int(hh), int(mm)


DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


# ------------------- 스케줄 판정 -------------------
def _should_run(job: Dict[str, Any], last_iso: str, now: _dt.datetime) -> bool:
    """주기별 실행여부 계산. now는 로컬시간."""
    interval = str(job.get("interval", "")).lower()
    last = _dt.datetime.fromisoformat(last_iso) if last_iso else None

    if interval == "daily":
        t = job.get("time")
        if not t:
            return False
        hh, mm = _parse_hhmm(t)
        target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if last is None:
            return now >= target
        return (last.date() < now.date()) and (now >= target)

    if interval == "weekly":
        day = str(job.get("day", "")).lower()
        t = job.get("time")
        if day not in DAYS or not t:
            return False
        hh, mm = _parse_hhmm(t)
        # 이번 주 가장 최근 해당 요일 시각
        offset = (DAYS.index(day) - now.weekday()) % 7
        target = now.replace(hour=hh, minute=mm, second=0, microsecond=0) + _dt.timedelta(
            days=offset
        )
        if target > now:
            target -= _dt.timedelta(days=7)
        if last is None:
            return now >= target
        # 마지막 실행이 target 이전이면 이번 주기 미실행
        return last < target and now >= target

    if interval == "hourly":
        minute = int(job.get("minute", 0))
        target = now.replace(minute=minute, second=0, microsecond=0)
        if target > now:
            target -= _dt.timedelta(hours=1)
        if last is None:
            return now >= target
        # 마지막 실행이 지난 타겟보다 이전이면 실행
        return last < target and now >= target

    return False


# ------------------- 잡 실행기 -------------------
def _run_job(job: Dict[str, Any]) -> None:
    """여기서 실제 작업 분기. 네 환경에 맞게만 바꿔라."""
    name = str(job.get("name"))
    _log(f"RUN {name} start")
    try:
        # VELOS 환경에 맞는 실제 스크립트 매핑
        if name == "DailyReport":
            subprocess.run(
                [sys.executable, os.path.join(ROOT, "scripts", "generate_velos_report_ko.py")],
                check=True,
            )
        elif name == "WeeklyAudit":
            subprocess.run(
                [sys.executable, os.path.join(ROOT, "scripts", "check_velos_stats.py")], check=True
            )
        elif name == "HealthCheck":
            subprocess.run(
                [sys.executable, os.path.join(ROOT, "scripts", "check_velos_stats.py")], check=True
            )
        else:
            _log(f"SKIP unknown job: {name}")
            return
        _log(f"RUN {name} ok")
    except Exception as e:
        _log(f"RUN {name} fail: {e}")


# ------------------- 내부 디스패처 -------------------
def run_internal_scheduler(argv: List[str]) -> None:
    """스케줄러 엔트리포인트. 5분마다 한 번 이걸 호출하면 끝."""
    # 인자 처리
    force = None
    frozen_now = None
    singleton = False
    log_dir = None

    if "--list" in argv:
        _ensure_default_jobs()
        jobs = _load_json(JOBS_FILE, [])
        for j in jobs:
            print(j)
        return

    if "--force" in argv:
        i = argv.index("--force")
        if i + 1 < len(argv):
            force = argv[i + 1]

    if "--now" in argv:
        i = argv.index("--now")
        if i + 1 < len(argv):
            frozen_now = _dt.datetime.fromisoformat(argv[i + 1])

    if "--singleton" in argv:
        singleton = True

    if "--log-dir" in argv:
        i = argv.index("--log-dir")
        if i + 1 < len(argv):
            log_dir = argv[i + 1]

    os.makedirs(DATA, exist_ok=True)
    _ensure_default_jobs()

    jobs = _load_json(JOBS_FILE, [])
    state = _load_json(STATE_FILE, {})

    now = frozen_now or _dt.datetime.now()  # 로컬시간

    updated = False
    for job in jobs:
        name = str(job.get("name"))
        last_iso = state.get(name)

        if force and name.lower() == force.lower():
            _run_job(job)
            state[name] = now.isoformat()
            updated = True
            continue

        if _should_run(job, last_iso, now):
            _run_job(job)
            state[name] = now.isoformat()
            updated = True

    if updated:
        _save_json(STATE_FILE, state)


# ------------------- 메인 -------------------
def _master_body():
    """
    네가 기존에 돌리던 '본체 작업'이 있으면 여기서 호출해라.
    현재는 스케줄링이 전부라서 비워둔다.
    """
    # 예: pass / 또는 기존 로직 import 후 실행
    pass


if __name__ == "__main__":
    # --singleton 플래그 수용
    singleton = "--singleton" in sys.argv
    if singleton and not acquire_lock():
        print("[VELOS] another instance detected; exiting")
        sys.exit(0)

    # 환경/경로 보정
    os.chdir(ROOT)

    print("[VELOS] master loop starting")

    try:
        run_internal_scheduler(sys.argv[1:])
    except Exception as _e:
        _log(f"[WARN] scheduler error: {_e}")
    # 본체가 더 할 일이 있으면 아래에서 실행
    try:
        _master_body()
    except Exception as e:
        _log(f"[WARN] master body error: {e}")
