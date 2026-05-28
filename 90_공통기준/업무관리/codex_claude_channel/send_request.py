#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def append_review(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write("\n" + text.rstrip() + "\n")


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Send Codex review request to Claude Code channel")
    parser.add_argument("--request", required=True)
    parser.add_argument("--review", required=True)
    parser.add_argument("--endpoint", default="http://127.0.0.1:8791/request")
    parser.add_argument("--timeout", type=int, default=10)
    args = parser.parse_args()

    request_path = Path(args.request)
    review_path = Path(args.review)
    content = request_path.read_text(encoding="utf-8")
    request_id = f"codex-{int(time.time())}"
    payload = {
        "request_id": request_id,
        "content": content,
        "review_path": str(review_path),
    }
    try:
        status, body = post_json(args.endpoint, payload, args.timeout)
    except (urllib.error.URLError, TimeoutError) as exc:
        append_review(
            review_path,
            f"""## {now()} - channel send FAIL

- request_id: `{request_id}`
- endpoint: `{args.endpoint}`
- reason: `{exc}`
- next_action: Start Claude with `codex_claude_channel/start_claude_channel.ps1`, then retry.
""",
        )
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    append_review(
        review_path,
        f"""## {now()} - channel send PASS

- request_id: `{request_id}`
- endpoint: `{args.endpoint}`
- http_status: {status}

```json
{body}
```
""",
    )
    print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
