import json
import os
import sqlite3
import sys

# 경로 하드코딩 제거, report_paths 모듈 사용
from modules.report_paths import ROOT, P`nsys.path.insert(0, str(ROOT))
os.environ.setdefault("VELOS_DB_WRITE_FORBIDDEN", "1")
import app.guards.db_write_guard  # noqa

DB = str(P("data/velos.db"))
OPS = str(P("data/logs/ops_patch_log.jsonl"))


def log(**rec):
    with open(OPS, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


con = sqlite3.connect(DB)
cur = con.cursor()
try:
    cur.execute("CREATE TABLE IF NOT EXISTS guard_test (ts TEXT)")
    con.commit()
    print("CREATE_OK")
    log(step="create", result="ok")
except Exception as e:
    print("CREATE_FAIL", type(e).__name__, str(e)[:120])
    log(step="create", result="fail", error=str(e))
    raise

try:
    cur.execute("INSERT INTO guard_test(ts) VALUES ('blocked')")
    con.commit()
    print("UNEXPECTED_INSERT_OK")
    log(step="insert", result="unexpected_ok")
except Exception as e:
    print("EXPECTED_INSERT_BLOCK", type(e).__name__, str(e)[:120])
    log(step="insert", result="blocked", error=str(e)[:120])


