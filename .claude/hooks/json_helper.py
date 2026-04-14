#!/usr/bin/env python3
"""json_helper.py — hook용 공용 JSON 설정 읽기 유틸 (세션46 GPT+Claude 합의).

safe_json_get(쉘 내장)은 경량 payload 추출용으로 유지.
이 스크립트는 설정 파일(hook_config.json 등)에서 중첩 키를 읽는 용도.

Usage:
  python3 json_helper.py <json_file> <dotted.key.path> [default]

Examples:
  python3 json_helper.py .claude/hook_config.json task_escalation.log_path ""
  python3 json_helper.py .claude/hook_config.json task_escalation.per_task.daily-routine 3
  python3 json_helper.py .claude/hook_config.json task_escalation.default_threshold 3
"""
import json
import sys


def get_nested(data: dict, key_path: str, default: str = "") -> str:
    """점(.) 구분 키 경로로 중첩 dict 값을 꺼낸다."""
    keys = key_path.split(".")
    current = data
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return default
    return str(current) if current is not None else default


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: json_helper.py <json_file> <dotted.key.path> [default]", file=sys.stderr)
        sys.exit(1)

    json_file = sys.argv[1]
    key_path = sys.argv[2]
    default = sys.argv[3] if len(sys.argv) > 3 else ""

    try:
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(default)
        sys.exit(0)

    print(get_nested(data, key_path, default))


if __name__ == "__main__":
    main()
