"""
from modules.core.time_utils import now_utc, now_kst, iso_utc, monotonic
import json
import subprocess
from pathlib import Path

def update_system_health():
    log_path = Path("C:/giwanos/data/logs/system_health.json")

    # 기본 상태
    status = {
        "timestamp": now_kst().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "Healthy",
        "summary": "System operating within normal parameters.",
        "level": "info",
        "diagnostics": {}
    }

    # VELOS_NTP_HOURLY 상태 점검
    try:
        info = subprocess.run(
            ["schtasks", "/Query", "/TN", "VELOS_NTP_HOURLY", "/V", "/FO", "LIST"],
            capture_output=True, text=True, encoding="cp437"
        ).stdout
        status["diagnostics"]["scheduled_task"] = {
            "VELOS_NTP_HOURLY": "OK" if "Last Result:                          0" in info else "CHECK"
        }
    except Exception as e:
        status["diagnostics"]["scheduled_task"] = {
            "VELOS_NTP_HOURLY": f"ERROR: {e}"
        }

    # 로그 저장
    log_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
