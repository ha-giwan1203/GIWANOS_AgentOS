#!/usr/bin/env python3
"""
hook_timing.jsonl 주간 집계 — Phase 2 진입 지표 측정 기반.

지표:
  1. 주간 경고/차단 빈도 (status가 warn/block_*/deny/phase1_warn인 레코드)
  2. 직전 주 대비 변동률 (Phase 2 진입 기준 < 20%)
  3. hook별 경고 상위 5종
  4. 세션당 평균 경고 수

사용법:
  python3 .claude/scripts/hook_timing_summary.py [--days N] [--compare]
  --days N   : 최근 N일 (기본 7)
  --compare  : 직전 N일과 비교 (변동률 계산)
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path


WARN_STATUSES = {"warn", "phase1_warn", "stale", "rebind_stale"}
BLOCK_PREFIX = "block_"
DENY_STATUSES = {"deny"}


def is_warn(status: str) -> bool:
    if status in WARN_STATUSES:
        return True
    if status.startswith(BLOCK_PREFIX):
        return True
    if status in DENY_STATUSES:
        return True
    return False


def load(path: Path, start: datetime, end: datetime):
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            ts_str = d.get("ts", "")
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except Exception:
                continue
            if start <= ts < end:
                records.append(d)
    return records


def summarize(records, label):
    total = len(records)
    warns = [r for r in records if is_warn(r.get("status", ""))]
    warn_count = len(warns)
    by_hook = Counter(r.get("hook", "") for r in warns)
    by_status = Counter(r.get("status", "") for r in warns)
    durations = [r.get("duration_ms", 0) for r in records if isinstance(r.get("duration_ms"), (int, float))]
    avg_duration = sum(durations) / len(durations) if durations else 0

    print(f"\n=== {label} ===")
    print(f"total records: {total}")
    print(f"warn/block/deny: {warn_count} ({warn_count/total*100:.1f}%)" if total else "warn/block/deny: 0")
    print(f"avg duration: {avg_duration:.0f}ms")
    print(f"\ntop 5 hooks by warn count:")
    for h, c in by_hook.most_common(5):
        print(f"  {h}: {c}")
    print(f"\ntop 5 warn statuses:")
    for s, c in by_status.most_common(5):
        print(f"  {s}: {c}")
    return warn_count


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--compare", action="store_true")
    p.add_argument("--path", default=".claude/hooks/hook_timing.jsonl")
    args = p.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"ERROR: {path} not found", file=sys.stderr)
        return 1

    now = datetime.now(timezone.utc)
    current_start = now - timedelta(days=args.days)
    records_current = load(path, current_start, now)
    current_warn = summarize(records_current, f"최근 {args.days}일")

    if args.compare:
        prev_start = now - timedelta(days=args.days * 2)
        prev_end = current_start
        records_prev = load(path, prev_start, prev_end)
        prev_warn = summarize(records_prev, f"직전 {args.days}일")

        if prev_warn > 0:
            delta_pct = abs(current_warn - prev_warn) / prev_warn * 100
        else:
            delta_pct = 0 if current_warn == 0 else float("inf")

        print(f"\n=== Phase 2 진입 지표 1 ===")
        print(f"경고 빈도 변동률: {delta_pct:.1f}%  (기준 < 20%)")
        passed = delta_pct < 20
        print(f"판정: {'PASS' if passed else 'FAIL'}")
        if prev_warn == 0 and current_warn > 0:
            print("주의: 직전 기간 경고 0건 — 기준 미달 아닌 데이터 부족")

    return 0


if __name__ == "__main__":
    sys.exit(main())
