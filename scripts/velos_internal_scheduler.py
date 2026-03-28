# ==== VELOS INTERNAL SCHEDULER BEGIN ====
import os, sys, json, subprocess, datetime as _dt
from typing import Dict, Any, List

ROOT = os.getenv("VELOS_ROOT", r"C:\giwanos")
DATA = os.path.join(ROOT, "data")
LOGD = os.path.join(DATA, "logs")
os.makedirs(LOGD, exist_ok=True)

JOBS_FILE  = os.path.join(DATA, "jobs.json")
STATE_FILE = os.path.join(DATA, "job_state.json")
RUN_LOG    = os.path.join(LOGD, "jobs.log")

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
            {"name": "DailyReport", "interval": "daily",  "time": "09:05"},
            {"name": "WeeklyAudit", "interval": "weekly", "day": "monday", "time": "09:30"},
            {"name": "HealthCheck", "interval": "hourly", "minute": 0},
        ]
        _save_json(JOBS_FILE, default_jobs)
        _log("jobs.json created with defaults")

def _parse_hhmm(s: str):
    hh, mm = s.split(":")
    return int(hh), int(mm)

DAYS = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]

def _should_run(job: Dict[str, Any], last_iso: str, now: _dt.datetime) -> bool:
    """주기별 실행여부 계산. now는 로컬시간."""
    interval = str(job.get("interval","")).lower()
    last = _dt.datetime.fromisoformat(last_iso) if last_iso else None

    if interval == "daily":
        t = job.get("time")
        if not t: return False
        hh, mm = _parse_hhmm(t)
        target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if last is None:
            return now >= target
        return (last.date() < now.date()) and (now >= target)

    if interval == "weekly":
        day = str(job.get("day","")).lower()
        t = job.get("time")
        if day not in DAYS or not t: return False
        hh, mm = _parse_hhmm(t)
        # 이번 주 가장 최근 해당 요일 시각
        offset = (DAYS.index(day) - now.weekday()) % 7
        target = now.replace(hour=hh, minute=mm, second=0, microsecond=0) + _dt.timedelta(days=offset)
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

def _run_job(job: Dict[str, Any]) -> None:
    """여기서 실제 작업 분기. 네 환경에 맞게만 바꿔라."""
    name = str(job.get("name"))
    _log(f"RUN {name} start")
    try:
        # 1) 내부 함수 호출식 예시 (권장: 같은 프로세스)
        # if name == "DailyReport":
        #     from your_module import run_daily_report
        #     run_daily_report()

        # 2) 외부 스크립트 호출식 예시 (PowerShell/py 혼용)
        if name == "DailyReport":
            subprocess.run(["pwsh", "-NoProfile", "-File", os.path.join(ROOT, "scripts", "report_daily.ps1")], check=True)
        elif name == "WeeklyAudit":
            subprocess.run(["pwsh", "-NoProfile", "-File", os.path.join(ROOT, "scripts", "weekly_audit.ps1")], check=True)
        elif name == "HealthCheck":
            subprocess.run(["pwsh", "-NoProfile", "-File", os.path.join(ROOT, "scripts", "health_check.ps1")], check=True)
        else:
            _log(f"SKIP unknown job: {name}")
            return
        _log(f"RUN {name} ok")
    except Exception as e:
        _log(f"RUN {name} fail: {e}")

def run_internal_scheduler(argv: List[str]) -> None:
    """스케줄러 엔트리포인트. 5분마다 한 번 이걸 호출하면 끝."""
    # 인자 처리
    force = None
    frozen_now = None
    if "--list" in argv:
        jobs = _load_json(JOBS_FILE, [])
        for j in jobs:
            print(j)
        return
    if "--force" in argv:
        i = argv.index("--force")
        if i+1 < len(argv): force = argv[i+1]
    if "--now" in argv:
        i = argv.index("--now")
        if i+1 < len(argv): frozen_now = _dt.datetime.fromisoformat(argv[i+1])

    os.makedirs(DATA, exist_ok=True)
    _ensure_default_jobs()

    jobs  = _load_json(JOBS_FILE, [])
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
# ==== VELOS INTERNAL SCHEDULER END ====

if __name__ == "__main__":
    run_internal_scheduler(sys.argv[1:])
