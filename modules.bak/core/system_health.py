import json, datetime, pathlib

SYSTEM_HEALTH_PATH = pathlib.Path("data/logs/system_health.json")
SYSTEM_HEALTH_PATH.parent.mkdir(parents=True, exist_ok=True)

def update_system_health():
    data = {
        "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "Healthy",
        "summary": "System operating within normal parameters.",
        "level": "info"
    }
    with open(SYSTEM_HEALTH_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


