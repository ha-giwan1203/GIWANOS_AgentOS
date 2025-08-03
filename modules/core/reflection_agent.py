"""ReflectionAgent – 실패/장애 이벤트를 요약·저장"""

import json, pathlib, datetime, logging

REFLECT_DIR = pathlib.Path("data/reflections")
REFLECT_DIR.mkdir(parents=True, exist_ok=True)
LOG = logging.getLogger("reflection_agent")

def reflect(event: dict):
    """
    event 예시:
      {
        "timestamp": "...",
        "category": "master_loop",
        "error": "TypeError: ...",
        "context": { ... }   # (선택)
      }
    """
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
    fname = REFLECT_DIR / f"reflection_{ts}.json"
    fname.write_text(json.dumps(event, ensure_ascii=False, indent=2), encoding="utf-8")
    LOG.info("Reflection saved → %s", fname)
    return fname
