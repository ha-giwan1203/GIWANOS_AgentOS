# [ACTIVE] VELOS 성능 벤치마크 스위트 (스크립트 복사본)
# VELOS 운영 철학 선언문: 파일명은 절대 변경하지 않는다. 수정 시 자가 검증을 포함하고,
# 실행 결과를 기록하며, 경로/구조는 불변으로 유지한다. 실패는 로깅하고 자동 복구를 시도한다.

from __future__ import annotations
import os
import time
import random
import string
import sqlite3
import threading
import statistics as stats
from dataclasses import dataclass

DB = os.environ.get("VELOS_DB_PATH", r"C:\giwanos\data\velos.db")

# ──────────────────────────────────────────────────────────────────────────────
# DB helpers
# ──────────────────────────────────────────────────────────────────────────────
def open_conn(db: str = DB) -> sqlite3.Connection:
    conn = sqlite3.connect(db, timeout=5, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def fts_match_count(conn: sqlite3.Connection, token: str) -> int:
    # FTS는 반드시 MATCH로
    return conn.execute(
        "SELECT COUNT(*) FROM memory_fts WHERE memory_fts MATCH ?",
        (token,)
    ).fetchone()[0]


# ──────────────────────────────────────────────────────────────────────────────
# Workloads
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class BenchResult:
    name: str
    n: int
    seconds: float
    qps: float
    extra: str = ""


def _rand_token() -> str:
    return random.choice(["alpha", "beta", "gamma", "delta", "kappa", "omega", "velos", "token5"])


def insert_n(n: int) -> BenchResult:
    conn = open_conn()
    cur = conn.cursor()
    t0 = time.time()
    for i in range(n):
        cur.execute(
            "INSERT INTO memory(ts, role, insight) VALUES(?,?,?)",
            (int(time.time()), "bench",
             f"bench row {i} {_rand_token()} " + "".join(random.choices(string.ascii_lowercase, k=8)))
        )
        # autocommit인데 너무 빠르면 WAL이 비대해질 수 있음. 2k마다 체크포인트 힌트.
        if (i+1) % 2000 == 0:
            try:
                cur.execute("PRAGMA wal_checkpoint(PASSIVE);")
            except sqlite3.Error:
                pass
    sec = time.time() - t0
    conn.close()
    return BenchResult("insert", n, sec, n/max(sec, 1e-6))


def search_k(k: int, limit: int = 25) -> BenchResult:
    conn = open_conn()
    cur = conn.cursor()
    tokens = [_rand_token() for _ in range(k)]
    t0 = time.time()
    counts = []
    for tok in tokens:
        rows = cur.execute(
            """
            SELECT m.id, m.ts FROM memory_fts f
            JOIN memory m ON m.id=f.rowid
            WHERE f.insight MATCH ? ORDER BY m.ts DESC LIMIT ?
            """, (tok, limit)
        ).fetchall()
        counts.append(len(rows))
    sec = time.time() - t0
    conn.close()
    extra = f"avg_hits={sum(counts)/len(counts):.1f}"
    return BenchResult("search", k, sec, k/max(sec, 1e-6), extra)


def update_n(n: int) -> BenchResult:
    conn = open_conn()
    cur = conn.cursor()
    ids = [r[0] for r in cur.execute(
        "SELECT id FROM memory WHERE role='bench' ORDER BY id DESC LIMIT ?", (n,)
    ).fetchall()]
    t0 = time.time()
    for i, mid in enumerate(ids):
        cur.execute("UPDATE memory SET insight=? WHERE id=?", (f"bench updated {_rand_token()}", mid))
        if (i+1) % 2000 == 0:
            try:
                cur.execute("PRAGMA wal_checkpoint(PASSIVE);")
            except sqlite3.Error:
                pass
    sec = time.time() - t0
    conn.close()
    return BenchResult("update", n, sec, n/max(sec, 1e-6))


def delete_role(role: str = "bench") -> BenchResult:
    conn = open_conn()
    cur = conn.cursor()
    n = cur.execute("SELECT COUNT(*) FROM memory WHERE role=?", (role,)).fetchone()[0]
    t0 = time.time()
    cur.execute("DELETE FROM memory WHERE role=?", (role,))
    sec = time.time() - t0
    conn.close()
    return BenchResult("delete", n, sec, n/max(sec, 1e-6))


# ──────────────────────────────────────────────────────────────────────────────
# Concurrency: N writer threads, M reader threads (each uses its own connection)
# ──────────────────────────────────────────────────────────────────────────────
def concurrent_mix(writers: int = 2, readers: int = 4, seconds: int = 5) -> BenchResult:
    stop = time.time() + seconds
    w_counts, r_counts, errs = [], [], []

    def w():
        c = open_conn()
        i = 0
        try:
            while time.time() < stop:
                c.execute("INSERT INTO memory(ts, role, insight) VALUES(?,?,?)",
                          (int(time.time()), "benchmix", f"mix write {_rand_token()}"))
                i += 1
        except Exception as e:
            errs.append(("w", str(e)))
        finally:
            w_counts.append(i)
            c.close()

    def r():
        c = open_conn()
        i = 0
        try:
            while time.time() < stop:
                _ = fts_match_count(c, _rand_token())
                i += 1
        except Exception as e:
            errs.append(("r", str(e)))
        finally:
            r_counts.append(i)
            c.close()

    threads = [threading.Thread(target=w) for _ in range(writers)] + \
              [threading.Thread(target=r) for _ in range(readers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    extra = f"writes/s={sum(w_counts)/seconds:.1f}, reads/s={sum(r_counts)/seconds:.1f}"
    if errs:
        extra += f", errors={errs!r}"
    return BenchResult("concurrent_mix", writers+readers, seconds, 0.0, extra)


# ──────────────────────────────────────────────────────────────────────────────
# Runner
# ──────────────────────────────────────────────────────────────────────────────
def run_suite():
    sizes = [2_000, 10_000, 50_000]  # 필요하면 늘려라. 네가 디스크를 믿는 만큼.
    results: list[BenchResult] = []

    # sanity
    conn = open_conn()
    mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
    sync = conn.execute("PRAGMA synchronous;").fetchone()[0]
    busy = conn.execute("PRAGMA busy_timeout;").fetchone()[0]
    print(f"[sanity] mode={mode}, sync={sync}, busy={busy}")
    conn.close()

    for n in sizes:
        print(f"\n=== insert {n} ===")
        r = insert_n(n)
        results.append(r)
        print(f"insert_{n}: {r.seconds:.2f}s ({r.qps:.0f}/s)")

        print(f"=== search {n//50} queries ===")
        r = search_k(n//50)
        results.append(r)
        print(f"search_{n//50}: {r.seconds:.3f}s ({r.qps:.0f}/s) {r.extra}")

        print(f"=== update {n//10} rows ===")
        r = update_n(n//10)
        results.append(r)
        print(f"update_{n//10}: {r.seconds:.2f}s ({r.qps:.0f}/s)")

    print("\n=== concurrent mix (writers=2, readers=4, 5s) ===")
    r = concurrent_mix(2, 4, 5)
    results.append(r)
    print(f"concurrent: {r.extra}")

    print("\n=== cleanup bench data ===")
    for role in ("bench", "benchmix"):
        r = delete_role(role)
        print(f"delete_{role}: n={r.n}, {r.seconds:.2f}s")
    
    # 백업 청소 화이트리스트: velos_*.bench.db만 삭제, velos_golden_*.db는 보호
    print("\n=== cleanup backup bench files ===")
    backup_dir = Path("backup")
    if backup_dir.exists():
        bench_files = list(backup_dir.glob("velos_*.bench.db"))
        golden_files = list(backup_dir.glob("velos_golden_*.db"))
        print(f"Found {len(bench_files)} bench files, {len(golden_files)} golden files (protected)")
        for f in bench_files:
            try:
                f.unlink()
                print(f"Deleted: {f.name}")
            except Exception as e:
                print(f"Failed to delete {f.name}: {e}")

    # Summary table
    print("\n====== SUMMARY ======")
    for r in results:
        print(f"{r.name:14} n={r.n:<7} t={r.seconds:>7.2f}s  rate={r.qps:>8.1f}/s  {r.extra}")


if __name__ == "__main__":
    run_suite()
