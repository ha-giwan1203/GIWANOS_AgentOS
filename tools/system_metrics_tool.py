import psutil, asyncio, datetime, logging
async def collect_metrics_async():
    await asyncio.sleep(0)
    res = {"ts": datetime.datetime.now().isoformat(timespec="seconds"),
           "cpu": psutil.cpu_percent(), "mem": psutil.virtual_memory().percent}
    logging.getLogger("tool_system_metrics").info(res)
    return res


