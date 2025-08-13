# VELOS DB Write Guard (authorizer)
import contextlib
import os
import sqlite3

FORBIDDEN = os.getenv("VELOS_DB_WRITE_FORBIDDEN") == "1"
ALLOW_BRIDGE = os.getenv("VELOS_ALLOW_BRIDGE") == "1"  # ← 우회 플래그

OK = getattr(sqlite3, "SQLITE_OK", 0)
DENY = getattr(sqlite3, "SQLITE_DENY", 1)

SQLITE_INSERT = getattr(sqlite3, "SQLITE_INSERT", 18)
SQLITE_UPDATE = getattr(sqlite3, "SQLITE_UPDATE", 23)
SQLITE_DELETE = getattr(sqlite3, "SQLITE_DELETE", 9)
SQLITE_ALTER_TABLE = getattr(sqlite3, "SQLITE_ALTER_TABLE", 26)
SQLITE_DROP_TABLE = getattr(sqlite3, "SQLITE_DROP_TABLE", 13)
SQLITE_DROP_INDEX = getattr(sqlite3, "SQLITE_DROP_INDEX", 11)
SQLITE_DROP_VIEW = getattr(sqlite3, "SQLITE_DROP_VIEW", 15)
SQLITE_DROP_TRIGGER = getattr(sqlite3, "SQLITE_DROP_TRIGGER", 17)

SQLITE_CREATE_TABLE = getattr(sqlite3, "SQLITE_CREATE_TABLE", 2)
SQLITE_CREATE_INDEX = getattr(sqlite3, "SQLITE_CREATE_INDEX", 1)
SQLITE_CREATE_VIEW = getattr(sqlite3, "SQLITE_CREATE_VIEW", 3)
SQLITE_CREATE_TRIGGER = getattr(sqlite3, "SQLITE_CREATE_TRIGGER", 6)

ALLOW_CREATE = {
    SQLITE_CREATE_TABLE,
    SQLITE_CREATE_INDEX,
    SQLITE_CREATE_VIEW,
    SQLITE_CREATE_TRIGGER,
}
BLOCK_GENERIC = {
    SQLITE_ALTER_TABLE,
    SQLITE_DROP_TABLE,
    SQLITE_DROP_INDEX,
    SQLITE_DROP_VIEW,
    SQLITE_DROP_TRIGGER,
}
SYSTEM_TABLES = {"sqlite_master", "sqlite_sequence"}
ALLOW_DML_TABLES = {"messages"}  # VELOS가 관리하는 테이블


def _authorizer(action, p1, p2, db_name, trigger_or_view):
    # 브리지 우회: 이 프로세스에서만 전면 허용
    if ALLOW_BRIDGE:
        return OK
    if not FORBIDDEN:
        return OK

    name = (p1 or "").strip().strip('"').lower()
    if action in ALLOW_CREATE:
        return OK
    if name in SYSTEM_TABLES:
        return OK
    if name in ALLOW_DML_TABLES and action in {
        SQLITE_INSERT,
        SQLITE_UPDATE,
        SQLITE_DELETE,
    }:
        return OK
    if action in BLOCK_GENERIC or action in {
        SQLITE_INSERT,
        SQLITE_UPDATE,
        SQLITE_DELETE,
    }:
        return DENY
    return OK


_orig_connect = sqlite3.connect


def _guarded_connect(*args, **kwargs):
    con = _orig_connect(*args, **kwargs)
    with contextlib.suppress(Exception):
        con.set_authorizer(_authorizer)
    return con


sqlite3.connect = _guarded_connect
