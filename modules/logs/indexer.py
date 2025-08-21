# [ACTIVE] VELOS 로그 인덱서 - 로그 처리 및 검색 모듈
# -*- coding: utf-8 -*-
import json
import os
import re
import time
from pathlib import Path

import pandas as pd

try:
    import pyarrow as pa
    import pyarrow.feather as feather

    HAVE_ARROW = True
except Exception:
    HAVE_ARROW = False

ROOT = Path(r"C:\giwanos")
DATA = ROOT / "data"
LOGS = DATA / "logs"
CACHE = LOGS / "_cache"
CACHE.mkdir(parents=True, exist_ok=True)

CONV_SOURCES = [
    LOGS / "learning_memory.jsonl",
    LOGS / "dialog_memory.jsonl",
    LOGS / "session_*.json",
]


def _read_sources(days: int, limit: int) -> pd.DataFrame:
    rows = []
    cutoff = time.time() - days * 86400
    for p in LOGS.glob("*.jsonl"):
        if p.stat().st_mtime < cutoff:
            continue
        for line in p.read_text("utf-8", errors="ignore").splitlines():
            try:
                o = json.loads(line)
                rows.append(o)
            except:
                pass
    for p in LOGS.glob("session_*.json"):
        if p.stat().st_mtime < cutoff:
            continue
        try:
            o = json.loads(p.read_text("utf-8", errors="ignore"))
            rows.extend(o if isinstance(o, list) else [o])
        except:
            pass
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.rename(
            columns={
                "timestamp": "time",
                "speaker": "role",
                "message": "content",
            }
        )
        # 필요한 컬럼 강제 보정
        for c in ["time", "role", "content", "session", "turn", "source_path"]:
            if c not in df.columns:
                df[c] = ""
        df = df.sort_values("time").tail(limit)
    return df


def load_conversations(days=7, limit=1000, role=None, query: str | None = None) -> pd.DataFrame:
    cache = CACHE / f"conv_{days}_{limit}.feather"
    if HAVE_ARROW and cache.exists() and (time.time() - cache.stat().st_mtime < 60):
        df = feather.read_feather(cache)
    else:
        df = _read_sources(days, limit)
        if HAVE_ARROW and not df.empty:
            feather.write_feather(df, cache)
    if role:
        df = df[df["role"] == role]
    if query:
        pat = re.compile(query, re.I)
        df = df[df["content"].astype(str).str.contains(pat)]
    return df.reset_index(drop=True)


def load_system_metrics():
    # 간단한 더미 – 필요시 실제 시스템 측정 코드로 교체
    return {"mem": "2.4 GB", "cpu": "23%", "sessions": "3"}
