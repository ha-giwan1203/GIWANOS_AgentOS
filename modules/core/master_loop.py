from modules.core.reflection_agent import reflect
from modules.core.time_utils import now_utc, now_kst, iso_utc, monotonic

try:
    report_path = await master.run()
except Exception as e:
    reflect({
        "timestamp": now_utc().isoformat()+"Z",
        "category": "master_loop",
        "error": str(e),
    })
    raise



