import psutil
from modules.core.error_handler import handle_exception

def get_latest_metrics() -> dict:
    try:
        return {
            "cpu": psutil.cpu_percent(interval=1),
            "memory": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage('/').percent
        }
    except Exception as e:
        handle_exception(e, context="최신 시스템 메트릭 조회 실패")
        return {}


