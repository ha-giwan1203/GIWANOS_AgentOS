# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

from __future__ import annotations

import argparse
import builtins
import importlib
import json
import os
import runpy
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional


# -----------------------------
# 경로 로딩
# -----------------------------
def _root() -> Path:
    root = os.getenv("VELOS_ROOT")
    if root and Path(root).is_dir():
        return Path(root)
    sett = os.getenv("VELOS_SETTINGS") or "/home/user/webapp/configs/settings.yaml"
    try:
        import yaml  # type: ignore

        y = yaml.safe_load(Path(sett).read_text(encoding="utf-8"))
        base = (y or {}).get("paths", {}).get("base_dir")
        if base and Path(base).is_dir():
            return Path(base)
    except Exception:
        pass
    return Path("/home/user/webapp") if Path("/home/user/webapp").is_dir() else Path.cwd()


ROOT = _root()
LOG_DIR = ROOT / "data" / "logs" / "runtime_trace"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


def _rel(p: str) -> Optional[str]:
    try:
        return str(Path(p).resolve().relative_to(ROOT))
    except Exception:
        return None


# -----------------------------
# 훅: import / open
# -----------------------------
class TraceSink:
    def __init__(self):
        ts = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        self.path = LOG_DIR / f"trace_{ts}.jsonl"
        self.f = self.path.open("a", encoding="utf-8")
        self.lock = threading.Lock()

    def write(self, rec: Dict[str, Any]):
        rec.setdefault("ts_iso", _now_iso())
        with self.lock:
            self.f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            self.f.flush()

    def close(self):
        try:
            self.f.close()
        except Exception:
            pass


SINK: Optional[TraceSink] = None
ORIG_IMPORT = builtins.__import__
ORIG_OPEN = builtins.open


def traced_import(name, globals=None, locals=None, fromlist=(), level=0):
    mod = ORIG_IMPORT(name, globals, locals, fromlist, level)
    try:
        if SINK:
            # 모듈 파일 경로 기록
            file = getattr(mod, "__file__", None)
            rel = _rel(file) if file else None
            SINK.write({"type": "import", "module": name, "file": rel or file or "N/A"})
    except Exception:
        pass
    return mod


def traced_open(file, mode="r", *args, **kwargs):
    try:
        rel = _rel(str(file))
        if SINK and rel:
            SINK.write({"type": "open", "file": rel, "mode": mode})
    except Exception:
        pass
    return ORIG_OPEN(file, mode, *args, **kwargs)


# -----------------------------
# 실행 시나리오
# -----------------------------
ENTRY_WARMLOAD = [
    "interface.velos_dashboard",
    "interface.status_dashboard",
    "modules.core.session_store",  # --selftest 대상
    "tools.analysis.file_usage_risk_audit",  # 리스크 감사 자체 임포트
]


def run_warmload():
    ok = True
    for m in ENTRY_WARMLOAD:
        try:
            importlib.import_module(m)
        except Exception as e:
            ok = False
            if SINK:
                SINK.write({"type": "error", "stage": "warmload", "module": m, "error": repr(e)})
    return 0 if ok else 1


def run_session_store_selftest():
    try:
        mod = importlib.import_module("modules.core.session_store")
        rc = mod.main(["--selftest"])
        return rc
    except Exception as e:
        if SINK:
            SINK.write({"type": "error", "stage": "session_store_selftest", "error": repr(e)})
        return 1


def run_script(script_path: str):
    # 무한 루프 방지: 타임아웃 타이머
    timer = threading.Timer(60.0, lambda: (_ for _ in ()).throw(TimeoutError("trace timeout")))
    timer.daemon = True
    timer.start()
    try:
        runpy.run_path(script_path, run_name="__main__")
        return 0
    except TimeoutError as e:
        if SINK:
            SINK.write({"type": "warn", "stage": "script", "msg": "timeout 60s, aborted"})
        return 0
    except SystemExit as e:
        return int(getattr(e, "code", 0) or 0)
    except Exception as e:
        if SINK:
            SINK.write({"type": "error", "stage": "script", "error": repr(e)})
        return 1
    finally:
        try:
            timer.cancel()
        except Exception:
            pass


def run_module(modname: str):
    timer = threading.Timer(60.0, lambda: (_ for _ in ()).throw(TimeoutError("trace timeout")))
    timer.daemon = True
    timer.start()
    try:
        runpy.run_module(modname, run_name="__main__")
        return 0
    except TimeoutError:
        if SINK:
            SINK.write({"type": "warn", "stage": "module", "msg": "timeout 60s, aborted"})
        return 0
    except SystemExit as e:
        return int(getattr(e, "code", 0) or 0)
    except Exception as e:
        if SINK:
            SINK.write({"type": "error", "stage": "module", "error": repr(e)})
        return 1
    finally:
        try:
            timer.cancel()
        except Exception:
            pass


# -----------------------------
# CLI
# -----------------------------
def main(argv=None) -> int:
    global SINK
    ap = argparse.ArgumentParser(description="VELOS runtime trace runner")
    ap.add_argument(
        "--mode", choices=["warmload", "selftests", "script", "module"], default="warmload"
    )
    ap.add_argument("--script", help="script path for --mode script")
    ap.add_argument("--module", help="module name for --mode module")
    args = ap.parse_args(argv)

    # 경로 주입
    sys.path.append(str(ROOT))

    # 훅 설치
    SINK = TraceSink()
    builtins.__import__ = traced_import
    builtins.open = traced_open

    try:
        if args.mode == "warmload":
            rc = run_warmload()
        elif args.mode == "selftests":
            rc = run_session_store_selftest()
        elif args.mode == "script":
            if not args.script:
                print("need --script")
                return 2
            rc = run_script(args.script)
        else:
            if not args.module:
                print("need --module")
                return 2
            rc = run_module(args.module)
        return rc
    finally:
        # 훅 해제
        builtins.__import__ = ORIG_IMPORT
        builtins.open = ORIG_OPEN
        if SINK:
            SINK.close()


if __name__ == "__main__":
    raise SystemExit(main())
