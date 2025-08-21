# [ACTIVE] VELOS 운영 철학 적용
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"/home/user/webapp")
HEALTH_PATH = ROOT / "data" / "logs" / "system_health.json"


def write_health(ok: bool, reason: str = "", targets=None):
    try:
        d = {}
        if HEALTH_PATH.exists():
            d = json.loads(HEALTH_PATH.read_text(encoding="utf-8") or "{}")
        d["dispatch_last_ok"] = bool(ok)
        d["dispatch_last_targets"] = list(
            sorted(set((targets or []) + (d.get("dispatch_last_targets") or [])))
        )
        d["dispatch_last_ts"] = datetime.now(timezone.utc).isoformat()
        if not ok:
            d["dispatch_last_error"] = reason
        tmp = HEALTH_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(HEALTH_PATH)
    except Exception:
        pass


def main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--body", required=True)
    ap.add_argument("--file", required=False)
    args = ap.parse_args()

    token = os.getenv("PUSHBULLET_API_TOKEN")
    device_nick = os.getenv("PUSHBULLET_DEVICE_NICK")
    if not token:
        print("[PUSHBULLET] missing PUSHBULLET_API_TOKEN")
        write_health(False, "missing token", ["pushbullet"])
        return 70

    try:
        from pushbullet import Pushbullet

        pb = Pushbullet(token)
        dev = None
        if device_nick:
            dev = next((d for d in pb.devices if d.nickname == device_nick), None)
        if args.file:
            p = Path(args.file)
            if p.exists():
                with p.open("rb") as f:
                    file_data = pb.upload_file(f, p.name)
                (dev or pb).push_file(**file_data, body=args.body, title=args.title)
            else:
                (dev or pb).push_note(args.title, f"{args.body}\n[file missing: {args.file}]")
        else:
            (dev or pb).push_note(args.title, args.body)
        print("[PUSHBULLET] ok")
        write_health(True, targets=["pushbullet"])
        return 0
    except Exception as e:
        print("[PUSHBULLET] failure:", e)
        write_health(False, f"send failure: {e}", ["pushbullet"])
        return 72


if __name__ == "__main__":
    sys.exit(main())
