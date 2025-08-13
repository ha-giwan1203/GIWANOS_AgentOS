from __future__ import annotations

import contextlib
import json
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(r"C:\giwanos")
DB = ROOT / "data" / "velos.db"
HEALTH = ROOT / "data" / "logs" / "system_health.json"
OUTDIR = ROOT / "data" / "reports"
OUTDIR.mkdir(parents=True, exist_ok=True)


def now_utc():
    return datetime.now(UTC)


def ymd():
    return now_utc().astimezone().strftime("%Y%m%d")


def count_since(sec: int) -> int:
    con = sqlite3.connect(DB)
    try:
        t = int(time.time()) - sec
        (n,) = con.execute("select count(*) from messages where created_utc>=?", (t,)).fetchone()
        return n
    finally:
        con.close()


def main():
    last5 = count_since(5 * 60)
    last60 = count_since(60 * 60)
    last24h = count_since(24 * 60 * 60)
    health = {}
    if HEALTH.exists():
        with contextlib.suppress(Exception):
            health = json.loads(HEALTH.read_text(encoding="utf-8"))

    out = OUTDIR / f"VELOS_Report_{ymd()}.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# VELOS Daily Report ({ymd()})\n\n")
        f.write("## Message Counters\n")
        f.write(f"- Last 5 minutes: **{last5}**\n")
        f.write(f"- Last 60 minutes: **{last60}**\n")
        f.write(f"- Last 24 hours: **{last24h}**\n\n")
        f.write("## Health Snapshot\n")
        f.write("```json\n")
        json.dump(health, f, ensure_ascii=False, indent=2)
        f.write("\n```\n")
    print(out)


if __name__ == "__main__":
    main()
