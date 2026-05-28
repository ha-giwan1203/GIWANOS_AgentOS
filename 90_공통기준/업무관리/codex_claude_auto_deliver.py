#!/usr/bin/env python3
"""Send a Codex review request to the current Claude session and record the result."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


CONFIG_PATH = Path(__file__).with_name("codex_claude_auto_delivery.json")


def now_kst() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M KST")


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise SystemExit(f"config_missing: {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def append_review(review_path: Path, text: str) -> None:
    review_path.parent.mkdir(parents=True, exist_ok=True)
    with review_path.open("a", encoding="utf-8", newline="\n") as f:
        f.write("\n" + text.rstrip() + "\n")


def parse_result(stdout: str) -> str:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return stdout.strip()
    for key in ("result", "message", "content", "text"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return json.dumps(payload, ensure_ascii=False, indent=2)


def post_json(url: str, payload: dict, timeout: int) -> tuple[int, str]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"content-type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read().decode("utf-8", errors="replace")


def deliver_via_channel(config: dict, request_path: Path, review_path: Path, timeout: int) -> int:
    endpoint = config.get("channel_endpoint") or "http://127.0.0.1:8791/request"
    request_id = f"codex-{int(time.time())}"
    payload = {
        "request_id": request_id,
        "content": request_path.read_text(encoding="utf-8"),
        "review_path": str(review_path),
    }
    try:
        status, body = post_json(endpoint, payload, timeout)
    except (urllib.error.URLError, TimeoutError) as exc:
        append_review(
            review_path,
            f"""## {now_kst()} - channel auto delivery FAIL

- mode: claude_code_channels_bridge
- request_id: `{request_id}`
- endpoint: `{endpoint}`
- reason: `{exc}`
- next_action: Start Claude with `90_공통기준/업무관리/codex_claude_channel/start_claude_channel.ps1`, then retry.
""",
        )
        print(f"channel_delivery_failed: {exc}", file=sys.stderr)
        return 2

    append_review(
        review_path,
        f"""## {now_kst()} - channel auto delivery PASS

- mode: claude_code_channels_bridge
- request_id: `{request_id}`
- endpoint: `{endpoint}`
- http_status: {status}

```json
{body}
```
""",
    )
    print(body)
    return 0


def deliver_via_resume(config: dict, request_path: Path, review_path: Path, session_id: str, timeout: int) -> int:
    if not config.get("resume_external_enabled"):
        append_review(
            review_path,
            f"""## {now_kst()} - resume auto delivery BLOCKED

- mode: claude_resume_print
- session_id: `{session_id}`
- reason: `{config.get("block_reason", "resume external delivery disabled")}`
- fallback: `{config.get("fallback", "local review queue")}`
""",
        )
        print("resume_external_delivery_disabled", file=sys.stderr)
        return 5

    prompt = request_path.read_text(encoding="utf-8")
    cmd = [
        "claude",
        "--resume",
        session_id,
        "--print",
        "--output-format",
        "json",
    ]

    proc = subprocess.run(
        cmd,
        input=prompt,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
    )

    parsed = parse_result(proc.stdout)
    status = "PASS" if proc.returncode == 0 else "FAIL"
    entry = f"""## {now_kst()} - resume auto delivery {status}

- mode: claude_resume_print
- authorized_by: {config.get("authorized_by", "")}
- session_id: `{session_id}`
- request: `{request_path}`
- command: `claude --resume <session_id> --print --output-format json`
- exit_code: {proc.returncode}

### parsed_result

```text
{parsed}
```

### stderr

```text
{proc.stderr.strip()}
```
"""
    append_review(review_path, entry)

    print(parsed)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Codex -> Claude review auto delivery")
    parser.add_argument("--request", required=True, help="request.md path")
    parser.add_argument("--review", required=True, help="review.md path")
    parser.add_argument("--mode", choices=["auto", "channel", "resume"], default="auto")
    parser.add_argument("--session-id", help="Claude session id override")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    config = load_config()
    if not config.get("enabled"):
        print("auto_delivery_disabled", file=sys.stderr)
        return 2

    request_path = Path(args.request)
    review_path = Path(args.review)
    if not request_path.exists():
        print(f"request_missing: {request_path}", file=sys.stderr)
        return 3

    session_id = args.session_id or config.get("session_id")
    if args.mode == "resume" and not session_id:
        print("session_id_missing", file=sys.stderr)
        return 4

    if args.mode in ("auto", "channel"):
        return deliver_via_channel(config, request_path, review_path, min(args.timeout, int(config.get("channel_timeout", 10))))

    return deliver_via_resume(config, request_path, review_path, session_id or "", args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
