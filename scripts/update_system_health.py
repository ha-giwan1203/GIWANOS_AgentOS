from __future__ import annotations

import json
import platform
import time
from datetime import datetime

try:
    import psutil
except Exception:
    psutil = None  # 없어도 죽지 않게

from modules.report_paths import ROOT
LOGS = ROOT / r"data\logs"
LOGS.mkdir(parents=True, exist_ok=True)


def main():
    uptime = None
    cpu = None
    mem = None
    if psutil:
        try:
            uptime = int(time.time() - psutil.boot_time())
            cpu = psutil.cpu_percent(interval=0.3)
            mem = getattr(psutil.virtual_memory(), "percent", None)
        except Exception:
            pass
    data = {
        "status": "OK",
        "host": platform.node(),
        "python": platform.python_version(),
        "uptime": uptime,
        "cpu_percent": cpu,
        "mem_percent": mem,
        "alerts": [],
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    (LOGS / "system_health.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("[OK] system_health.json 갱신")


if __name__ == "__main__":
    main()

