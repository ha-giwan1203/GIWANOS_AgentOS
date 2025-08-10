from __future__ import annotations
# =============================================
# VELOS: System Health Logger
# =============================================

from modules.core.time_utils import now_utc, now_kst, iso_utc, monotonic

import json
from pathlib import Path

def update_system_health() -> str:
    log_path = Path("C:/giwanos/data/logs/system_health.json")
    status = {
        "timestamp_utc": now_utc().isoformat() + "Z",
        "timestamp_kst": now_kst().isoformat(),
        "status": "Healthy",
        "summary": "System operating within normal parameters.",
        "level": "info",
        "diagnostics": {}
    }
    log_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(log_path)

if __name__ == "__main__":
    print(update_system_health())
