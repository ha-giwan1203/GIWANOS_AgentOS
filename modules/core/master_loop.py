from modules.core.reflection_agent import reflect

try:
    report_path = await master.run()
except Exception as e:
    reflect({
        "timestamp": datetime.datetime.utcnow().isoformat()+"Z",
        "category": "master_loop",
        "error": str(e),
    })
    raise
