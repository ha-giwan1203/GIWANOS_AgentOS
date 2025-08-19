# [ACTIVE] VELOS 마스터 스케줄러 - 중앙 작업 관리 시스템
# VELOS 운영 철학 선언문
# "판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다."

# 카나리아 헬스체크 - 프로세스 시작 시 자체 점검
import subprocess
import sys

def canary_healthcheck():
    """FTS 헬스체크 수행 및 필요시 긴급 복구"""
    try:
        # 환경 변수 설정
        os.environ["VELOS_DB_PATH"] = os.environ.get("VELOS_DB_PATH", r"C:\giwanos\data\velos.db")
        
        # 1차 헬스체크
        result = subprocess.run([
            sys.executable, 
            os.path.join(os.path.dirname(__file__), "py", "fts_healthcheck.py")
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode != 0:
            print(f"[WARN] FTS healthcheck failed → emergency recovery...")
            print(f"Error: {result.stderr}")
            print("FTS_HEALTH failed")
            
            # 긴급 복구 실행
            recovery_result = subprocess.run([
                sys.executable,
                os.path.join(os.path.dirname(__file__), "py", "fts_emergency_recovery.py")
            ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
            
            if recovery_result.returncode != 0:
                print(f"[ERROR] Emergency recovery failed: {recovery_result.stderr}")
                return False
            
            # 2차 헬스체크
            result2 = subprocess.run([
                sys.executable,
                os.path.join(os.path.dirname(__file__), "py", "fts_healthcheck.py")
            ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
            
            if result2.returncode != 0:
                print(f"[ERROR] FTS healthcheck failed after recovery: {result2.stderr}")
                return False
            
            print("[INFO] Emergency recovery successful")
            print("FTS_RECOVERY applied")
        
        print("FTS_HEALTH ok")
        return True
        
    except Exception as e:
        print(f"[ERROR] Canary healthcheck failed: {e}")
        print("FTS_HEALTH failed")
        return False

# 시작 시 카나리아 헬스체크 실행
if not canary_healthcheck():
    print("[FATAL] Canary healthcheck failed - exiting")
    sys.exit(1)
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
  --dry-run              실행하지 않고 판정만 출력
  --verbose              상세 로그 출력
"""

import os
import sys
import json
import subprocess
import atexit
import datetime as _dt
from typing import Dict, Any, List
from pathlib import Path

# VELOS 공용 설정 유틸리티 사용
try:
    # 현재 디렉토리를 sys.path에 추가
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    
    from modules.utils.settings_bootstrap import VELOS_ROOT, LOG_PATH
    ROOT = str(VELOS_ROOT)
    
    # VELOS 모듈 import (안전화)
    try:
        from modules.core.session_store import append_session_event
        from modules.core.velos_session_init import init_velos_session
        VELOS_AVAILABLE = True
    except ImportError:
        VELOS_AVAILABLE = False
        print("[WARN] VELOS modules not available, running in standalone mode")
        
except ImportError:
    # 폴백: 기본 설정 사용
    ROOT = os.getenv("VELOS_ROOT", r"C:\giwanos")
    if ROOT not in sys.path:
        sys.path.append(ROOT)
    VELOS_AVAILABLE = False
    print("[WARN] settings_bootstrap not available, using fallback")

# ------------------- 경로/파일 -------------------
DATA = Path(ROOT) / "data"
LOGD = Path(ROOT) / "data" / "logs" if 'LOG_PATH' not in locals() else LOG_PATH
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
def _log(msg: str, level: str = "INFO"):
    """VELOS 스타일 로깅"""
    ts = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{ts}] [{level}] {msg}"
    
    # 파일 로그
    with open(RUN_LOG, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")
    
    # VELOS 세션 이벤트 기록
    if VELOS_AVAILABLE:
        try:
            append_session_event(
                text=msg,
                from_="scheduler",
                kind="job" if "RUN" in msg else "system",
                insight=f"스케줄러 {level.lower()}",
                tags=["master_scheduler", level.lower()]
            )
        except Exception as e:
            print(f"[WARN] VELOS session append failed: {e}")

def _load_json(path, default) -> Any:
    """안전한 JSON 로딩"""
    try:
        with open(str(path), "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        _log(f"File not found: {path}, using default", "WARN")
        return default
    except Exception as e:
        _log(f"JSON load error ({path}): {e}", "ERROR")
        return default

def _save_json(path, obj: Any) -> bool:
    """원자적 JSON 저장"""
    try:
        path_str = str(path)
        tmp = path_str + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path_str)
        return True
    except Exception as e:
        _log(f"JSON save error ({path}): {e}", "ERROR")
        return False

def _ensure_default_jobs() -> None:
    """기본 잡 설정 생성"""
    if not os.path.exists(JOBS_FILE):
        default_jobs = [
            {"name": "DailyReport", "interval": "daily", "time": "09:05"},
            {"name": "WeeklyAudit", "interval": "weekly", "day": "monday", "time": "09:30"},
            {"name": "HealthCheck", "interval": "hourly", "minute": 0},
            {"name": "MemoryCleanup", "interval": "daily", "time": "03:00"},
            {"name": "SnapshotBackup", "interval": "weekly", "day": "sunday", "time": "02:00"},
            {"name": "BridgeDispatch", "interval": "hourly", "minute": 30},
            {"name": "SnapshotCatalog", "interval": "daily", "time": "03:03"},
            {"name": "SnapshotIntegrity", "interval": "daily", "time": "03:07"},
            {"name": "SessionMerge", "interval": "hourly", "minute": 15},
        ]
        if _save_json(JOBS_FILE, default_jobs):
            _log("jobs.json created with VELOS defaults")

def _parse_hhmm(s: str) -> tuple[int, int]:
    """HH:MM 파싱"""
    try:
        hh, mm = s.split(":")
        return int(hh), int(mm)
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid time format: {s}")

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
        try:
            hh, mm = _parse_hhmm(t)
            target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
            if last is None:
                return now >= target
            return (last.date() < now.date()) and (now >= target)
        except ValueError:
            _log(f"Invalid time format in job {job.get('name')}: {t}", "ERROR")
            return False

    elif interval == "weekly":
        day = str(job.get("day", "")).lower()
        t = job.get("time")
        if day not in DAYS or not t:
            return False
        try:
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
        except ValueError:
            _log(f"Invalid time format in job {job.get('name')}: {t}", "ERROR")
            return False

    elif interval == "hourly":
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
def _run_job(job: Dict[str, Any], dry_run: bool = False) -> bool:
    """VELOS 환경에 맞는 작업 실행"""
    name = str(job.get("name"))
    
    if dry_run:
        _log(f"DRY-RUN {name} (would execute)")
        return True
    
    _log(f"RUN {name} start")
    
    try:
        # VELOS 스크립트 매핑
        script_map = {
            "DailyReport": "generate_velos_report_ko.py",
            "WeeklyAudit": "check_velos_stats.py", 
            "HealthCheck": "check_velos_stats.py",
            "MemoryCleanup": "memory_tick.py",
            "SnapshotBackup": "create_velos_snapshot.py",
            "BridgeDispatch": "velos_bridge.py",
            "SnapshotCatalog": "snapshot_catalog.py",
            "SnapshotIntegrity": "verify_snapshots.py",
            "SessionMerge": "velos_session_merge.bat",
            "BenchmarkDaily": "benchmark_regression.py",
        }
        
        script_path = script_map.get(name)
        if not script_path:
            _log(f"SKIP unknown job: {name}", "WARN")
            return False
            
        full_path = os.path.join(ROOT, "scripts", script_path)
        if not os.path.exists(full_path):
            _log(f"Script not found: {full_path}", "ERROR")
            return False
            
        # 모든 작업을 완전히 숨겨진 창에서 실행
        if script_path.endswith('.ps1'):
            result = subprocess.run([
                "pwsh", "-NoProfile", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", full_path
            ], capture_output=True, text=True, timeout=300, creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
        elif script_path.endswith('.bat'):
            result = subprocess.run([
                "cmd", "/c", full_path
            ], capture_output=True, text=True, timeout=300, creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
        else:
            # Python 스크립트는 pythonw.exe로 실행하여 창 숨김
            pythonw_exe = sys.executable.replace("python.exe", "pythonw.exe")
            if not os.path.exists(pythonw_exe):
                pythonw_exe = sys.executable  # fallback
            result = subprocess.run([
                pythonw_exe, full_path
            ], capture_output=True, text=True, timeout=300, creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
            
        if result.returncode == 0:
            _log(f"RUN {name} ok")
            return True
        else:
            _log(f"RUN {name} failed (exit={result.returncode}): {result.stderr}", "ERROR")
            return False
            
    except subprocess.TimeoutExpired:
        _log(f"RUN {name} timeout", "ERROR")
        return False
    except Exception as e:
        _log(f"RUN {name} exception: {e}", "ERROR")
        return False

# ------------------- 내부 디스패처 -------------------
def run_internal_scheduler(argv: List[str]) -> int:
    """스케줄러 엔트리포인트. 5분마다 한 번 이걸 호출하면 끝."""
    # 인자 처리
    force = None
    frozen_now = None
    dry_run = False
    verbose = False

    if "--list" in argv:
        _ensure_default_jobs()
        jobs = _load_json(JOBS_FILE, [])
        print("등록된 잡 목록:")
        for j in jobs:
            print(f"  - {j.get('name')}: {j.get('interval')} {j.get('time', j.get('minute', ''))}")
        return 0

    if "--force" in argv:
        i = argv.index("--force")
        if i+1 < len(argv):
            force = argv[i+1]

    if "--now" in argv:
        i = argv.index("--now")
        if i+1 < len(argv):
            try:
                frozen_now = _dt.datetime.fromisoformat(argv[i+1])
            except ValueError:
                print(f"Invalid datetime format: {argv[i+1]}")
                return 1

    if "--dry-run" in argv:
        dry_run = True

    if "--verbose" in argv:
        verbose = True

    # VELOS 세션 초기화
    if VELOS_AVAILABLE:
        try:
            _hot = init_velos_session()
            if verbose:
                print(f"[VELOS] Session ready: {_hot.get('session_id', 'N/A')}")
        except Exception as e:
            _log(f"VELOS session init failed: {e}", "WARN")

    os.makedirs(DATA, exist_ok=True)
    _ensure_default_jobs()

    jobs = _load_json(JOBS_FILE, [])
    state = _load_json(STATE_FILE, {})

    now = frozen_now or _dt.datetime.now()  # 로컬시간

    if verbose:
        print(f"[SCHEDULER] Current time: {now}")
        print(f"[SCHEDULER] Jobs loaded: {len(jobs)}")
        print(f"[SCHEDULER] State entries: {len(state)}")

    updated = False
    executed_count = 0
    
    for job in jobs:
        name = str(job.get("name"))
        last_iso = state.get(name)

        if force and name.lower() == force.lower():
            if _run_job(job, dry_run):
                state[name] = now.isoformat()
                updated = True
                executed_count += 1
            continue

        if _should_run(job, last_iso, now):
            if _run_job(job, dry_run):
                state[name] = now.isoformat()
                updated = True
                executed_count += 1

    if updated:
        if _save_json(STATE_FILE, state):
            _log(f"Scheduler completed: {executed_count} jobs executed")
        else:
            _log("Failed to save job state", "ERROR")
            return 1
    else:
        _log("No jobs executed")

    return 0


# ------------------- 메인 -------------------
def _master_body() -> None:
    """
    VELOS 마스터 루프 본체 작업
    기존 run_giwanos_master_loop.py의 핵심 로직을 여기서 실행
    """
    if not VELOS_AVAILABLE:
        _log("VELOS modules not available, skipping master body", "WARN")
        return
        
    try:
        # 기존 마스터 루프 로직을 여기서 실행
        # (필요시 run_giwanos_master_loop.py의 핵심 부분을 import)
        _log("Master body execution completed")
    except Exception as e:
        _log(f"Master body error: {e}", "ERROR")

if __name__ == "__main__":
    # --singleton 플래그 수용
    singleton = ("--singleton" in sys.argv)
    if singleton and not acquire_lock():
        print("[VELOS] another instance detected; exiting")
        sys.exit(0)

    # 환경/경로 보정
    os.chdir(ROOT)
    
    print("[VELOS] master loop starting")
    
    try:
        exit_code = run_internal_scheduler(sys.argv[1:])
        if exit_code != 0:
            sys.exit(exit_code)
    except Exception as e:
        _log(f"Scheduler error: {e}", "ERROR")
        sys.exit(1)
    
    # 본체가 더 할 일이 있으면 아래에서 실행
    try:
        _master_body()
    except Exception as e:
        _log(f"Master body error: {e}", "ERROR")
