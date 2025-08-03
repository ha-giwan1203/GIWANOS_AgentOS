from __future__ import annotations
import json, pathlib, datetime, psutil

try:
    import GPUtil
except ImportError:
    GPUtil = None

TEMPLATE: dict[str, float | str] = {
    "timestamp": "",
    "cpu_percent": 0.0,
    "memory_percent": 0.0,
    "disk_percent": 0.0,
    "gpu_percent": 0.0,
    "net_sent_mb": 0.0,
    "net_recv_mb": 0.0,
}

ROOT = pathlib.Path(__file__).resolve().parents[3]
LOG_FILE = ROOT / "data" / "logs" / "system_health.json"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def current_stats() -> dict:
    s = TEMPLATE.copy()
    s["timestamp"] = datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    s["cpu_percent"] = psutil.cpu_percent(interval=0.2)
    s["memory_percent"] = psutil.virtual_memory().percent
    s["disk_percent"] = psutil.disk_usage(str(ROOT)).percent
    if GPUtil:
        try:
            gpu = GPUtil.getGPUs()[0]
            s["gpu_percent"] = round(gpu.load * 100, 2)
        except Exception:
            pass
    io = psutil.net_io_counters()
    s["net_sent_mb"] = round(io.bytes_sent / 1_048_576, 2)
    s["net_recv_mb"] = round(io.bytes_recv / 1_048_576, 2)
    return s

def append_log() -> dict:
    entry = current_stats()
    try:
        if LOG_FILE.exists():
            data = json.loads(LOG_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data = [data]
        else:
            data = []
    except Exception:
        data = []
    data.append(entry)
    LOG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return entry

if __name__ == "__main__":
    rec = append_log()
    print("Logged one entry:", rec)

def update_system_health():
    # 상태 업데이트를 위한 래퍼 함수
    return append_log()