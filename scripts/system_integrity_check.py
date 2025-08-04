import os
import json
from pathlib import Path

GIWANOS_ROOT = Path("C:/giwanos")

required_paths = {
    "config_rules": GIWANOS_ROOT / "configs/judgment_rules.json",
    "learning_memory": GIWANOS_ROOT / "data/memory/learning_memory.json",
    "api_cost_log": GIWANOS_ROOT / "data/logs/api_cost_log.json",
    "logs": GIWANOS_ROOT / "data/logs",
    "memory": GIWANOS_ROOT / "data/memory",
    "reflections": GIWANOS_ROOT / "data/reflections",
    "reports": GIWANOS_ROOT / "data/reports",
    "snapshots": GIWANOS_ROOT / "data/snapshots"
}

def check_paths():
    print("\n[경로 검사 결과]")
    for name, path in required_paths.items():
        if not path.exists():
            print(f"[ERROR] Missing required path: {name} at {path}")
        else:
            print(f"[OK] Found: {name} at {path}")

def validate_json():
    json_files = [
        "configs/judgment_rules.json",
        "configs/system_config.json",
        "configs/fallback_stats.json",
        "data/logs/api_cost_log.json",
        "data/memory/learning_memory.json",
        "data/memory/identity_memory.json"
    ]

    print("\n[JSON 파일 검사 결과]")
    for json_file in json_files:
        try:
            with open(GIWANOS_ROOT / json_file, "r", encoding="utf-8") as file:
                json.load(file)
            print(f"[OK] Valid JSON: {json_file}")
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON syntax error in {json_file}: {e}")
        except FileNotFoundError:
            print(f"[ERROR] File not found: {json_file}")

def main():
    check_paths()
    validate_json()

if __name__ == "__main__":
    main()
