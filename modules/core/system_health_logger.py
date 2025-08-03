# core/system_health_logger.py
import json
import psutil
import datetime

def update_system_health():
    status = {
        "timestamp": datetime.datetime.now().isoformat(),
        "cpu_usage_percent": psutil.cpu_percent(interval=1),
        "memory_usage_percent": psutil.virtual_memory().percent,
        "disk_usage_percent": psutil.disk_usage('/').percent,
        "active_process_count": len(psutil.pids())
    }
    
    with open('C:/giwanos/data/logs/system_health.json', 'w', encoding='utf-8') as file:
        json.dump(status, file, indent=4)

if __name__ == "__main__":
    update_system_health()
