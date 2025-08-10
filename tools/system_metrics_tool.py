import psutil, asyncio, datetime, logging
from modules.core.time_utils import now_utc, now_kst, iso_utc, monotonic
async def collect_metrics_async():
    await asyncio.sleep(0)
    res = {"ts": now_utc().isoformat(timespec="seconds"),
           "cpu": psutil.cpu_percent(), "mem": psutil.virtual_memory().percent}
    logging.getLogger("tool_system_metrics").info(res)
    return res



