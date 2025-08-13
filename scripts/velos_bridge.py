# VELOS 운영 철학 선언문
from __future__ import annotations

import argparse
import contextlib
import json
import os
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

GIWANOS = Path("C:/giwanos")
DB_PATH = GIWANOS / "data" / "velos.db"
BUF_PATH = GIWANOS / "data" / "memory" / "memory_buffer.jsonl"
HEALTH_PATH = GIWANOS / "data" / "logs" / "system_health.json"
OPS_LOG = GIWANOS / "data" / "logs" / "ops_patch_log.jsonl"


# ----- 시간 유틸 -----
def utc_ts_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def utc_ts_int() -> int:
    return int(datetime.now(UTC).timestamp())


def local_dt():
    return datetime.now().astimezone()


def local_ts_iso() -> str:
    return local_dt().isoformat(timespec="seconds")


def local_tz_name() -> str:
    return local_dt().tzname() or "LOCAL"


def local_utc_offset_seconds() -> int:
    return int(local_dt().utcoffset().total_seconds())


# ----- 로깅 -----
def log_op(**rec):
    try:
        OPS_LOG.parent.mkdir(parents=True, exist_ok=True)
        rec.setdefault("timestamp", utc_ts_iso())  # backward compat (UTC)
        rec.setdefault("timestamp_local", local_ts_iso())  # local
        rec.setdefault("local_tz", local_tz_name())
        rec.setdefault("local_utc_offset_sec", local_utc_offset_seconds())
        with open(OPS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ----- DB 준비 -----
def ensure_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    con.execute("""
    CREATE TABLE IF NOT EXISTS messages(
      conversation_id TEXT,
      message_id TEXT PRIMARY KEY,
      role TEXT,
      body TEXT,
      created_utc INTEGER,
      author_device TEXT,
      client_seq INTEGER,
      edit_of TEXT NULL,
      meta_json TEXT,
      idempotency_key TEXT UNIQUE
    );
    """)
    con.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_dedupe ON messages(idempotency_key);")
    con.execute(
        "CREATE INDEX IF NOT EXISTS ix_conv_order ON messages(conversation_id, created_utc, client_seq);"
    )
    con.commit()
    return con


# ----- 버퍼 I/O -----
def append_jsonl_line(obj: dict) -> None:
    BUF_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, ensure_ascii=False)
    with open(BUF_PATH, "a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())


def flush_buffer_to_db(con: sqlite3.Connection) -> int:
    BUF_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not BUF_PATH.exists():
        return 0
    before = con.total_changes
    with con, open(BUF_PATH, encoding="utf-8") as f:
        for raw in f:
            s = raw.strip()
            if not s:
                continue
            try:
                rec = json.loads(s)
            except Exception:
                log_op(action="ingest_line_parse_fail", line=s[:200])
                continue
            rec.setdefault("created_utc", utc_ts_int())
            rec.setdefault("client_seq", 0)
            rec.setdefault("author_device", "unknown")
            rec.setdefault("role", "user")
            rec.setdefault("body", "")
            rec.setdefault("meta_json", None)
            rec.setdefault("edit_of", None)
            try:
                con.execute(
                    """
                    INSERT OR IGNORE INTO messages(
                      conversation_id, message_id, role, body, created_utc, author_device,
                      client_seq, edit_of, meta_json, idempotency_key
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rec.get("conversation_id"),
                        rec.get("message_id"),
                        rec.get("role"),
                        rec.get("body"),
                        rec.get("created_utc"),
                        rec.get("author_device"),
                        rec.get("client_seq"),
                        rec.get("edit_of"),
                        json.dumps(rec.get("meta_json"))
                        if rec.get("meta_json") is not None
                        else None,
                        rec.get("idempotency_key"),
                    ),
                )
            except sqlite3.IntegrityError:
                # 멱등 충돌은 무시
                pass
    inserted = con.total_changes - before
    with contextlib.suppress(Exception):
        open(BUF_PATH, "w", encoding="utf-8").close()
    return inserted


# ----- 헬스 파일 -----
def write_health(ok: bool, **extra):
    HEALTH_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        # 기존 필드 유지(레거시 호환)
        "status": "OK" if ok else "ERROR",
        "bridge_flush_ok": bool(ok),
        "timestamp": utc_ts_iso(),  # UTC(기존)
        # 확장 필드
        "timestamp_utc": utc_ts_iso(),
        "timestamp_local": local_ts_iso(),
        "local_tz": local_tz_name(),
        "local_utc_offset_sec": local_utc_offset_seconds(),
        "epoch_utc": utc_ts_int(),
    }
    payload.update(extra)
    with open(HEALTH_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


# ----- CLI -----
def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true", help="DB/헬스 점검만 수행")
    ap.add_argument("--ingest", metavar="BODY", help="버퍼에 메시지 1건 기록 후 즉시 flush")
    ap.add_argument("--idempotency", metavar="KEY", help="멱등 키(미지정시 자동 생성)")
    ap.add_argument("--room", default="roomA", help="대화방 id 기본값")
    ap.add_argument("--user", default="local", help="작성자 디바이스")
    args = ap.parse_args(argv)

    con = ensure_db()

    if args.probe and not args.ingest:
        write_health(True, inserted=0, mode="probe")
        log_op(action="probe", result="ok")
        return 0

    if args.ingest is not None:
        idem = args.idempotency or f"idemp-{uuid.uuid4().hex}"
        mid = f"m-{uuid.uuid4().hex}"
        rec = {
            "conversation_id": args.room,
            "message_id": mid,
            "role": "user",
            "body": args.ingest,
            "created_utc": utc_ts_int(),
            "author_device": args.user,
            "client_seq": 0,
            "idempotency_key": idem,
        }
        append_jsonl_line(rec)
        log_op(
            action="ingest",
            room=args.room,
            user=args.user,
            idempotency_key=idem,
            body_preview=args.ingest[:40],
        )

    inserted = flush_buffer_to_db(con)
    write_health(True, inserted=inserted, mode="flush")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
