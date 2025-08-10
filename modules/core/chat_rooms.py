# -*- coding: utf-8 -*-
from __future__ import annotations
import os, hashlib, time
from dataclasses import dataclass

def _sha(s: str, n: int = 24) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:n]

def base_room_id() -> str:
    rid = (os.getenv("ROOM_BASE_ID") or "").strip()
    if rid:
        return rid[:24]
    seed = f"{os.getenv('VELOS_NAMESPACE','velos')}:{os.getenv('COMPUTERNAME','host')}:{os.getenv('USERNAME','user')}"
    return _sha(seed, 24)

def sub_room_id(project: str | None = None, topic: str | None = None) -> str:
    base = base_room_id()
    if os.getenv("ROOM_ALLOW_SUBROOM","1") != "1":
        return base
    key = ":".join([base] + [x for x in [project, topic] if x])
    return _sha(key, 24)

@dataclass
class RolloverPolicy:
    max_turns: int = int(os.getenv("ROOM_ROLLOVER_TURNS", "200") or "200")
    max_ctx_tokens: int = int(os.getenv("ROOM_ROLLOVER_MAXTOK", "10000") or "10000")

def fresh_room(ttl_min: int | None = None) -> str:
    ttl = int(ttl_min or os.getenv("ROOM_FRESH_TTL_MIN","60"))
    key = f"{base_room_id()}:fresh:{int(time.time() // (ttl*60))}"
    return _sha(key, 24)
