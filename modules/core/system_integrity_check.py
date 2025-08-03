import os
import json
from pathlib import Path

GIWANOS_ROOT = Path("C:/giwanos")

required_paths = {
    "config_rules": GIWANOS_ROOT / "config/judgment_rules.json",
    "core_rules": GIWANOS_ROOT / "core/judgment_rules.json",
    "memory": GIWANOS_ROOT / "memory",
    "logs": GIWANOS_ROOT / "data/logs",
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
        "config/judgment_rules.json",
        "core/judgment_rules.json",
        "config/system_config.json",
        "config/fallback_stats.json"
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
