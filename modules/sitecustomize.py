# [ACTIVE] VELOS 사이트커스터마이즈 - Python 환경 초기화 모듈
from __future__ import annotations

import atexit
import json
import os
import sys
import time
import traceback
from pathlib import Path

# UTF-8 인코딩 강제 설정 (모든 Python 프로세스에 적용)
for stream in ("stdout", "stderr"):
    s = getattr(sys, stream, None)
    try:
        s.reconfigure(encoding="utf-8")
    except Exception:
        pass

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# ---- optional .env loader (opt-in via VELOS_LOAD_ENV=1) ----
if os.getenv("VELOS_LOAD_ENV") == "1":
    for p in (Path("C:\giwanos/configs/.env"), Path("configs/.env"), Path(".env")):
        try:
            if p.exists():
                try:
                    from dotenv import load_dotenv

                    load_dotenv(p, override=True, encoding="utf-8")
                except Exception:
                    for ln in p.read_text(encoding="utf-8").splitlines():
                        if ln.strip() and not ln.lstrip().startswith("#") and "=" in ln:
                            k, v = ln.split("=", 1)
                            os.environ[k.strip()] = v.strip()
                break
        except Exception:
            pass

ROOT = Path(os.getenv("VELOS_ROOT", r"C:\giwanos")).resolve()
DATA = ROOT / "data"
LOGS = DATA / "logs"
REPORTS = DATA / "reports" / "auto"
CURSOR_LOOP = LOGS / "loop_state_tracker.json"
CURSOR_REPORT = DATA / "reports" / "report_cursor.json"
CURSOR_MEM = DATA / "memory" / "memory_cursor.json"

for d in [LOGS, REPORTS, CURSOR_MEM.parent]:
    d.mkdir(parents=True, exist_ok=True)


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


def _w(path, obj):
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


# 초기 기록
_stage = os.getenv("VELOS_STAGE") or "INIT"
try:
    _w(
        CURSOR_LOOP,
        {
            "status": "STARTED",
            "stage": _stage,
            "started_at": _now(),
            "pid": os.getpid(),
            "argv": sys.argv,
        },
    )
    if not CURSOR_MEM.exists():
        _w(CURSOR_MEM, {"created": _now(), "last_read_pos": 0})
except Exception:
    pass

# 테스트용 강제 실패 플래그
_fail_flag = LOGS / "force_fail.flag"
if _fail_flag.exists():
    try:
        _w(
            CURSOR_LOOP,
            {"status": "FAILED", "stage": _stage, "failed_at": _now(), "reason": "force_fail.flag"},
        )
    finally:
        sys.exit(1)


def _finalize_success():
    latest = None
    if REPORTS.exists():
        files = sorted(REPORTS.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        if files:
            f = files[0]
            latest = {"path": str(f), "mtime": int(f.stat().st_mtime)}
            try:
                _w(CURSOR_REPORT, {"latest": latest, "updated_at": _now()})
            except Exception:
                pass
    try:
        _w(
            CURSOR_LOOP,
            {
                "status": "SUCCEEDED",
                "stage": os.getenv("VELOS_STAGE") or _stage,
                "ended_at": _now(),
                "latest_report": latest,
            },
        )
    except Exception:
        pass


def _finalize_failure(exc_type, exc, tb):
    try:
        _w(
            CURSOR_LOOP,
            {
                "status": "FAILED",
                "stage": os.getenv("VELOS_STAGE") or _stage,
                "failed_at": _now(),
                "error": "".join(traceback.format_exception(exc_type, exc, tb))[:2000],
            },
        )
    except Exception:
        pass


atexit.register(_finalize_success)


def _exh(t, e, b):
    _finalize_failure(t, e, b)
    sys.__excepthook__(t, e, b)


sys.excepthook = _exh
