# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

from __future__ import annotations

import io
import json
import os
import sys
import time
import traceback
import uuid
from typing import Any, Dict, Iterable, Optional

try:
    import yaml  # pyyaml
except Exception:
    yaml = None  # 없어도 실행되게 방어

# ----------------------------
# 경로 해석: 하드코딩 금지
# 우선순위: ENV(개별) > settings.yaml > ENV(루트) > 기본 루트(C:\giwanos)
# ----------------------------


def _safe_join(*parts: str) -> str:
    return os.path.normpath(os.path.join(*parts))


def _read_yaml(path: str) -> dict:
    if not path or not os.path.isfile(path) or not yaml:
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _resolve_root() -> str:
    # 최상위 루트: VELOS_ROOT 환경변수 우선
    root = os.getenv("VELOS_ROOT")
    if root and os.path.isdir(root):
        return root
    # settings.yaml의 base_dir
    settings_path = os.getenv("VELOS_SETTINGS") or _safe_join(
        "C:", os.sep, "giwanos", "configs", "settings.yaml"
    )
    cfg = _read_yaml(settings_path)
    base = (cfg.get("paths") or {}).get("base_dir")
    if base and os.path.isdir(base):
        return base
    # 최후의 기본값 (유지보수 편의상) - 절대 경로 하드코딩 회피 불가 상황 방어
    fallback = _safe_join("C:", os.sep, "giwanos")
    return fallback if os.path.isdir(fallback) else os.getcwd()


def _paths() -> dict:
    root = _resolve_root()
    cfg = _read_yaml(os.getenv("VELOS_SETTINGS") or _safe_join(root, "configs", "settings.yaml"))

    def pick(env_key: str, cfg_keys: Iterable[str], default_rel: str) -> str:
        v = os.getenv(env_key)
        if v:
            return v
        cur = cfg
        for k in cfg_keys:
            if isinstance(cur, dict) and k in cur:
                cur = cur[k]
            else:
                cur = None
                break
        if isinstance(cur, str) and cur:
            return cur
        return _safe_join(root, default_rel)

    return {
        "root": root,
        "sessions_jsonl": pick(
            "VELOS_SESSIONS_JSONL",
            ["paths", "sessions_jsonl"],
            _safe_join("data", "memory", "sessions.log.jsonl"),
        ),
        "memory_jsonl": pick(
            "VELOS_MEMORY_JSONL",
            ["paths", "memory_jsonl"],
            _safe_join("data", "memory", "learning_memory.jsonl"),
        ),
        "memory_json": pick(
            "VELOS_MEMORY_JSON",
            ["paths", "memory_json"],
            _safe_join("data", "memory", "learning_memory.json"),
        ),
        "snapshots_dir": pick(
            "VELOS_SNAP_DIR", ["paths", "snapshots_dir"], _safe_join("data", "snapshots")
        ),
        "logs_dir": pick("VELOS_LOGS_DIR", ["paths", "logs_dir"], _safe_join("data", "logs")),
    }


# ----------------------------
# 세션 이벤트 append-only JSONL
# 스키마: {ts, session_id, from, kind, text, insight, tags}
# ----------------------------


def _ensure_dir(path: str) -> None:
    d = path if os.path.splitext(path)[1] == "" else os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)


def _now_ts() -> float:
    return time.time()


def _iso(ts: Optional[float] = None) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(ts or _now_ts()))


def append_session_event(
    text: str,
    from_: str,
    kind: str = "message",
    insight: Optional[str] = None,
    tags: Optional[Iterable[str]] = None,
    session_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    P = _paths()
    record = {
        "ts": _now_ts(),
        "ts_iso": _iso(),
        "session_id": session_id or os.getenv("VELOS_SESSION_ID") or f"session_{int(_now_ts())}",
        "from": from_,
        "kind": kind,
        "text": text,
        "insight": insight,
        "tags": list(tags or []),
    }
    if extra:
        record.update(extra)

    line = json.dumps(record, ensure_ascii=False)
    _ensure_dir(P["sessions_jsonl"])

    # 쓰기 + 즉시 검증
    with open(P["sessions_jsonl"], "a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())

    # tail 검증
    try:
        with open(P["sessions_jsonl"], "rb") as rf:
            rf.seek(-min(4096, rf.seek(0, io.SEEK_END) or 0), io.SEEK_END)
            tail = rf.read().decode("utf-8", errors="ignore").splitlines()[-1]
        parsed = json.loads(tail)
        for k in ("ts", "ts_iso", "from", "kind", "text"):
            assert k in parsed, f"missing key: {k}"
    except Exception as e:
        raise RuntimeError(f"[session_store] write verification failed: {e}")

    return record


# ----------------------------
# 메모리 병합: sessions.log.jsonl -> learning_memory.jsonl(+json)
# ----------------------------


def _iter_jsonl(path: str) -> Iterable[dict]:
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                yield json.loads(ln)
            except Exception:
                continue


def merge_sessions_into_memory(limit: Optional[int] = None) -> Dict[str, Any]:
    P = _paths()
    _ensure_dir(P["memory_jsonl"])
    _ensure_dir(P["memory_json"])

    # 세션 이벤트를 메모리 형식으로 투영
    def to_mem(evt: dict) -> dict:
        return {
            "ts": evt.get("ts"),
            "ts_iso": evt.get("ts_iso"),
            "session_id": evt.get("session_id"),
            "from": evt.get("from"),
            "insight": evt.get("insight") or evt.get("text"),
            "tags": evt.get("tags") or [],
            "kind": evt.get("kind"),
        }

    count = 0
    appended = 0
    seen = set()
    mem_lines: list[str] = []

    # 기존 메모리 라인 수 파악
    existing = 0
    if os.path.isfile(P["memory_jsonl"]):
        with open(P["memory_jsonl"], "r", encoding="utf-8") as f:
            existing = sum(1 for _ in f)

    # 기존 메모리에서 이미 처리된 항목들 수집
    for evt in _iter_jsonl(P["memory_jsonl"]):
        key = f'{evt.get("ts")}::{evt.get("session_id")}::{evt.get("from")}::{evt.get("kind")}'
        seen.add(key)

    # 새로운 세션 이벤트 처리
    for evt in _iter_jsonl(P["sessions_jsonl"]):
        count += 1
        key = f'{evt.get("ts")}::{evt.get("session_id")}::{evt.get("from")}::{evt.get("kind")}'
        if key in seen:
            continue
        seen.add(key)
        mem = to_mem(evt)
        mem_lines.append(json.dumps(mem, ensure_ascii=False))
        if limit and appended >= limit:
            break
        appended += 1

    # 새로운 항목들을 JSONL에 추가
    if mem_lines:
        with open(P["memory_jsonl"], "a", encoding="utf-8") as f:
            f.write("\n".join(mem_lines) + "\n")
            f.flush()
            os.fsync(f.fileno())

    # 요약 JSON 재생성(최근 N개만)
    N = 5000
    items = []
    for row in _iter_jsonl(P["memory_jsonl"]):
        items.append(row)
    items = items[-N:]
    with open(P["memory_json"], "w", encoding="utf-8") as jf:
        json.dump({"items": items, "count": len(items)}, jf, ensure_ascii=False, indent=2)

    return {
        "scanned": count,
        "existing_lines": existing,
        "appended": appended,
        "memory_count": len(items),
    }


# ----------------------------
# 스냅샷 저장
# ----------------------------


def write_session_snapshot() -> str:
    P = _paths()
    _ensure_dir(P["snapshots_dir"])
    snap_name = f"session_snapshot_{int(_now_ts())}_{uuid.uuid4().hex[:6]}.json"
    out = _safe_join(P["snapshots_dir"], snap_name)

    data = list(_iter_jsonl(P["sessions_jsonl"]))
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"count": len(data), "events": data[-10000:]}, f, ensure_ascii=False, indent=2)

    # 검증: 파일 존재 + 최소 필드 확인
    if not os.path.isfile(out):
        raise RuntimeError("[session_store] snapshot write failed")
    return out


# ----------------------------
# CLI 진입점 (자가 검증/데모)
# ----------------------------


def _print(s: str) -> None:
    sys.stdout.write(s + "\n")
    sys.stdout.flush()


def main(argv: Optional[Iterable[str]] = None) -> int:
    argv = list(argv or sys.argv[1:])
    try:
        if not argv or argv[0] in {"--help", "-h"}:
            _print(
                "usage: python -m modules.core.session_store [--append-demo] [--merge] [--snapshot] [--selftest]"
            )
            return 0

        if "--append-demo" in argv:
            rec = append_session_event(
                text="demo append",
                from_="system",
                kind="heartbeat",
                insight="demo",
                tags=["demo", "heartbeat"],
                extra={"level": "info"},
            )
            _print(f"[append] {rec['ts_iso']} ok")

        if "--merge" in argv:
            res = merge_sessions_into_memory()
            _print(
                f"[merge] scanned={res['scanned']} appended={res['appended']} memory={res['memory_count']}"
            )

        if "--snapshot" in argv:
            path = write_session_snapshot()
            _print(f"[snapshot] {path}")

        if "--selftest" in argv:
            # 1) append
            r1 = append_session_event(
                text="selftest-1", from_="system", kind="test", tags=["selftest"]
            )
            # 2) merge
            r2 = merge_sessions_into_memory()
            # 3) snapshot
            p = write_session_snapshot()
            # 결과 요약
            _print(
                f"[selftest] append_ts={r1['ts_iso']} merge_appended={r2['appended']} snapshot={os.path.basename(p)}"
            )
        return 0
    except Exception:
        _print("[error]\n" + traceback.format_exc())
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
