# VELOS 운영 철학 선언문
from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(r"C:\giwanos\data\velos.db")


def run():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=NORMAL;")
    cur.execute("""
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
    # 멱등 보장 + 정렬 최적화
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_dedupe ON messages(idempotency_key);")
    cur.execute(
        "CREATE INDEX IF NOT EXISTS ix_conv_order ON messages(conversation_id, created_utc, client_seq);"
    )
    con.commit()
    con.close()
    print("migration ok")


if __name__ == "__main__":
    run()
