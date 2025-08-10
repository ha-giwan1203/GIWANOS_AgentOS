
import os
import json

def load_system_status():
    path = "C:/giwanos/data/logs/system_health.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.dumps(json.load(f), indent=2, ensure_ascii=False)
    return "시스템 상태 로그 파일이 없습니다."

def load_latest_reflection():
    reflection_dir = "C:/giwanos/data/reflections"
    if not os.path.exists(reflection_dir):
        return "리플렉션 디렉토리가 없습니다."

    files = sorted(
        [f for f in os.listdir(reflection_dir) if f.endswith(".json")],
        key=lambda x: os.path.getmtime(os.path.join(reflection_dir, x)),
        reverse=True,
    )
    if not files:
        return "리플렉션 파일이 없습니다."

    latest = files[0]
    with open(os.path.join(reflection_dir, latest), "r", encoding="utf-8") as f:
        return json.dumps(json.load(f), indent=2, ensure_ascii=False)


