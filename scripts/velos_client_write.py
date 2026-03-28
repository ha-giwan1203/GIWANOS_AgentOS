# VELOS 운영 철학 선언문
from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import UTC, datetime

from modules.report_paths import ROOT
GIWANOS = ROOT
BUF_PATH = GIWANOS / "data" / "memory" / "memory_buffer.jsonl"
META_PATH = GIWANOS / "data" / "memory" / "client_seq.json"


def utc_ts() -> int:
    return int(datetime.now(UTC).timestamp())


def load_seq(room: str, user: str) -> int:
    META_PATH.parent.mkdir(parents=True, exist_ok=True)
    if META_PATH.exists():
        try:
            data = json.loads(META_PATH.read_text(encoding="utf-8"))
            return int(data.get(f"{room}:{user}", 0))
        except Exception:
            pass
    return 0


def save_seq(room: str, user: str, seq: int) -> None:
    data = {}
    if META_PATH.exists():
        try:
            data = json.loads(META_PATH.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    data[f"{room}:{user}"] = seq
    META_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def append_jsonl(obj: dict) -> None:
    BUF_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, ensure_ascii=False)
    # 윈도우: 단순 append + flush + fsync로 내구성 확보
    with open(BUF_PATH, "a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())


def write_message(room: str, body: str, user: str = "local") -> str:
    seq = load_seq(room, user) + 1
    save_seq(room, user, seq)
    mid = f"m-{uuid.uuid4().hex}"
    idem = f"idemp-{uuid.uuid4().hex}"
    rec = {
        "conversation_id": room,
        "message_id": mid,
        "role": "user",
        "body": body,
        "created_utc": utc_ts(),
        "author_device": user,
        "client_seq": seq,
        "idempotency_key": idem,
    }
    append_jsonl(rec)
    return idem


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("usage: velos_client_write.py <room_id> <body> [user_id]", file=sys.stderr)
        return 2
    room, body = argv[1], argv[2]
    user = argv[3] if len(argv) > 3 else "local"
    idem = write_message(room, body, user)
    print(idem)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
