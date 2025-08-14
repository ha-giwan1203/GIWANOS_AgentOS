from __future__ import annotations

import sqlite3
import time

from modules.report_paths import P
DB = P("data/velos.db")
OUT = P("data/backups")
OUT.mkdir(parents=True, exist_ok=True)
ts = time.strftime("%Y%m%d_%H%M%S")
dst = OUT / f"velos_{ts}.db"

src = sqlite3.connect(DB)
dstcon = sqlite3.connect(dst)
with dstcon:
    src.backup(dstcon)
src.close()
dstcon.close()
print(dst)

