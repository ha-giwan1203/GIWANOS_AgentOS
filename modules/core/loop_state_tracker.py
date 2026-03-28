# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

from __future__ import annotations
import os, json, time, socket, psutil
from pathlib import Path

ROOT = Path(os.getenv("VELOS_ROOT", "C:/giwanos"))
OUT  = ROOT / "data" / "reports" / "loop_state_tracker.json"

def heartbeat(status="ok", note=""):
    """VELOS 루프 상태 heartbeat 기록"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    j = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
        "host": socket.gethostname(),
        "pid": os.getpid(),
        "cpu": psutil.cpu_percent(interval=None),
        "mem": psutil.virtual_memory().percent,
        "status": status,
        "note": note,
    }
    OUT.write_text(json.dumps(j, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    heartbeat("test", "loop_state_tracker test run")
