import asyncio, logging
class ToolManager:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.logger = logging.getLogger("tool_manager")
        self.registry = {"system_metrics": ("tools.system_metrics_tool", "collect_metrics_async")}
    async def _dispatch(self, spec):
        mod_path, fn_name = self.registry[spec["tool"]]
        mod = __import__(mod_path, fromlist=[fn_name])
        async with self.lock:
            return await getattr(mod, fn_name)(**spec.get("args", {}))
    async def run_tasks(self, specs):
        return await asyncio.gather(*(self._dispatch(s) for s in specs), return_exceptions=True)


