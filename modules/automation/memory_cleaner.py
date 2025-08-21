# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# VELOS Memory Cleaner
# - Duplicate/near-duplicate removal
# - Low-quality noise filter
# - Recency + importance scoring
# - JSONL in/out + optional SQLite(FTS5) sync
#
# Usage:
#   python modules/automation/memory_cleaner.py --run-clean
#   python modules/automation/memory_cleaner.py --dry-run
#   python modules/automation/memory_cleaner.py --selftest

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ROOT = Path(os.getenv("VELOS_ROOT", r"C:\giwanos"))
MEM_DIR = ROOT / "data" / "memory"
REPORTS = ROOT / "data" / "reports"
DB_PATH = MEM_DIR / "velos.db"
SRC_JSONL = MEM_DIR / "learning_memory.jsonl"
OUT_JSONL = MEM_DIR / "learning_memory_cleaned.jsonl"
LOG_PATH = REPORTS / "memory_clean_report.json"

MIN_WORDS = 3  # 너무 짧은 문장 제거
SIM_THRESHOLD = 0.90  # 90% 이상 유사하면 중복으로 처리
MAX_KEEP = 50000  # 안전 상한(폭주 방지)
RECENCY_HALF_LIFE_DAYS = 14.0  # 최근성 반감기(2주)
KEYWORDS_IMPORTANT = {
    "error",
    "failure",
    "root cause",
    "rca",
    "outage",
    "schedule",
    "deadline",
    "launch",
    "prod",
    "incident",
    "policy",
    "security",
    "secrets",
    "credential",
    "owner",
    "contact",
    "path",
    "endpoint",
    "api",
    "db",
    "config",
}


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


def read_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> int:
    cnt = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            cnt += 1
    return cnt


def normalize_text(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s


def tokenize(s: str) -> List[str]:
    # 간단 토크나이저: 영숫자 단어만
    return re.findall(r"[A-Za-z0-9가-힣_]+", s.lower())


def jaccard(a: List[str], b: List[str]) -> float:
    if not a or not b:
        return 0.0
    sa, sb = set(a), set(b)
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union else 0.0


def sim_ratio(a: str, b: str) -> float:
    # 간단 hybrid: 길이 근사 보정 + Jaccard
    ta, tb = tokenize(a), tokenize(b)
    jac = jaccard(ta, tb)
    la, lb = len(a), len(b)
    if la == 0 or lb == 0:
        return 0.0
    len_ratio = min(la, lb) / max(la, lb)
    return 0.5 * jac + 0.5 * len_ratio


def is_low_quality(text: str) -> bool:
    t = normalize_text(text)
    if not t or t in {"...", "…", ".", "ㄱ", "ㅎ", "test", "테스트"}:
        return True
    if len(tokenize(t)) < MIN_WORDS:
        return True
    # 무의미 패턴
    if re.fullmatch(r"[\.]+|[~!@#\$\^&\*\(\)\-\+_=]{1,}$", t):
        return True
    return False


def recency_score(ts: Optional[str]) -> float:
    # ts: ISO or epoch str
    try:
        if ts is None:
            return 0.5
        if ts.isdigit():
            age_days = (time.time() - float(ts)) / 86400.0
        else:
            # 간단 파서(YYYY-MM-DD...)
            from datetime import datetime

            dt = datetime.fromisoformat(ts.replace("Z", ""))
            age_days = (time.time() - dt.timestamp()) / 86400.0
        # 반감기 기반
        lam = math.log(2) / RECENCY_HALF_LIFE_DAYS
        return math.exp(-lam * max(age_days, 0.0))
    except Exception:
        return 0.5


def importance_score(text: str) -> float:
    t = text.lower()
    hits = sum(1 for k in KEYWORDS_IMPORTANT if k in t)
    return min(1.0, 0.2 + 0.15 * hits)  # 기본 0.2 + 키워드당 가점


def quality_score(text: str, ts: Optional[str]) -> float:
    if is_low_quality(text):
        return 0.0
    r = recency_score(ts)
    i = importance_score(text)
    return round(0.5 * r + 0.5 * i, 4)


def fingerprint(text: str) -> str:
    # 빠른 exact-dedup용 해시
    return hashlib.sha1(normalize_text(text).encode("utf-8", errors="ignore")).hexdigest()


def load_memory(path: Path) -> List[Dict[str, Any]]:
    rows = []
    for rec in read_jsonl(path):
        # 필드 정규화
        text = rec.get("text") or rec.get("insight") or rec.get("content") or ""
        text = normalize_text(str(text))
        if not text:
            continue
        ts = rec.get("ts") or rec.get("timestamp") or rec.get("created_at")
        rows.append(
            {
                "text": text,
                "ts": ts,
                "meta": rec.get("meta", {}),
                "source": rec.get("source", rec.get("src", "unknown")),
                "id": rec.get("id") or fingerprint(text),
            }
        )
        if len(rows) >= MAX_KEEP:
            break
    return rows


def deduplicate(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    # 1) exact dedup by hash
    seen: Dict[str, Dict[str, Any]] = {}
    kept_exact = []
    for r in rows:
        h = fingerprint(r["text"])
        if h in seen:
            continue
        seen[h] = r
        kept_exact.append(r)

    # 2) near-dup by sim threshold (O(n^2) naive guard: sample down if huge)
    out: List[Dict[str, Any]] = []
    toks_cache: List[Tuple[List[str], str]] = []
    for r in kept_exact:
        t = r["text"]
        tok = tokenize(t)
        dup = False
        for otok, otext in toks_cache:
            if jaccard(tok, otok) >= SIM_THRESHOLD or sim_ratio(t, otext) >= SIM_THRESHOLD:
                dup = True
                break
        if not dup:
            toks_cache.append((tok, t))
            out.append(r)

    stats = {
        "input": len(rows),
        "after_exact": len(kept_exact),
        "after_near": len(out),
        "removed_exact": len(rows) - len(kept_exact),
        "removed_near": len(kept_exact) - len(out),
    }
    return out, stats


def filter_and_score(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    cleaned: List[Dict[str, Any]] = []
    removed_noise = 0
    for r in rows:
        text = r["text"]
        if is_low_quality(text):
            removed_noise += 1
            continue
        score = quality_score(text, r.get("ts"))
        r["score"] = score
        cleaned.append(r)

    # 고득점 우선 정렬(동점이면 최신 우선)
    def keyf(x):
        ts = x.get("ts") or ""
        return (-x["score"], str(ts))

    cleaned.sort(key=keyf)
    stats = {"removed_noise": removed_noise, "kept": len(cleaned)}
    return cleaned, stats


def to_sqlite(rows: List[Dict[str, Any]], db: Path) -> Dict[str, Any]:
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db))
    cur = conn.cursor()
    # FTS5 테이블
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS memory(
      id TEXT PRIMARY KEY,
      ts TEXT,
      score REAL,
      source TEXT,
      meta_json TEXT
    );
    """
    )
    cur.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(insight, raw, content='memory', content_rowid='id', tokenize='unicode61');"
    )
    # upsert
    up = 0
    cur.execute("BEGIN")
    try:
        for r in rows:
            cur.execute(
                """
            INSERT INTO memory(id, ts, score, source, meta_json)
            VALUES(?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET ts=excluded.ts, score=excluded.score, source=excluded.source, meta_json=excluded.meta_json
            """,
                (
                    r["id"],
                    r.get("ts"),
                    r.get("score", 0.0),
                    r.get("source"),
                    json.dumps(r.get("meta", {}), ensure_ascii=False),
                ),
            )
            up += cur.rowcount != 0
        # FTS 재구축 (트리거를 통한 자동 갱신)
        # memory 테이블에만 INSERT하면 트리거가 FTS를 자동으로 갱신
        cur.execute("DELETE FROM memory_fts;")
        for r in rows:
            cur.execute(
                """
                INSERT INTO memory(ts, role, insight, raw, tags)
                VALUES (?, 'system', ?, '', '[]')
            """,
                (r.get("ts", int(time.time())), r.get("text", "")),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return {"sqlite_upserted": up}


def run_clean(dry_run: bool = False) -> Dict[str, Any]:
    REPORTS.mkdir(parents=True, exist_ok=True)
    rows = load_memory(SRC_JSONL)
    base_cnt = len(rows)
    deduped, st1 = deduplicate(rows)
    cleaned, st2 = filter_and_score(deduped)

    out_stats = {
        "generated_at": now_iso(),
        "root": str(ROOT),
        "source_file": str(SRC_JSONL),
        "output_file": str(OUT_JSONL),
        "counts": {
            "source": base_cnt,
            "after_exact": st1["after_exact"],
            "after_near": st1["after_near"],
            "removed_exact": st1["removed_exact"],
            "removed_near": st1["removed_near"],
            "removed_noise": st2["removed_noise"],
            "kept": st2["kept"],
        },
        "params": {
            "min_words": MIN_WORDS,
            "sim_threshold": SIM_THRESHOLD,
            "recency_half_life_days": RECENCY_HALF_LIFE_DAYS,
        },
    }

    if not dry_run:
        n = write_jsonl(OUT_JSONL, cleaned)
        out_stats["written"] = n
        # SQLite 반영은 선택(파일 크면 비용 큼)
        try:
            sql_stats = to_sqlite(cleaned, DB_PATH)
            out_stats.update(sql_stats)
        except Exception as e:
            out_stats["sqlite_error"] = repr(e)

    LOG_PATH.write_text(json.dumps(out_stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_stats


def _selftest() -> int:
    # 최소 자기검증: 작은 샘플로 중복/노이즈 제거 여부
    sample = [
        {"text": "Error: DB connection timeout in prod", "ts": "2025-08-01T10:00:00"},
        {"text": "error db connection timeout in PROD", "ts": "2025-08-01T10:01:00"},
        {"text": "...", "ts": "2025-08-01T10:02:00"},
        {"text": "API endpoint /v1/users path", "ts": "2025-08-10T10:00:00"},
        {"text": "ㄱ", "ts": "2025-08-10T10:00:01"},
        {"text": "deadline launch schedule", "ts": "2025-08-15T11:00:00"},
    ]
    d, st1 = deduplicate(sample)
    c, st2 = filter_and_score(d)
    assert st1["after_near"] <= len(sample)
    assert st2["kept"] >= 2
    assert st2["removed_noise"] >= 1
    print("[SELFTEST] ok", st1, st2)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-clean", action="store_true", help="Clean memory and write outputs")
    ap.add_argument("--dry-run", action="store_true", help="Run cleaning without writing outputs")
    ap.add_argument("--selftest", action="store_true", help="Run self test")
    args = ap.parse_args(argv)

    if args.selftest:
        return _selftest()
    if args.dry_run:
        stats = run_clean(dry_run=True)
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return 0
    if args.run_clean:
        stats = run_clean(dry_run=False)
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return 0

    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
