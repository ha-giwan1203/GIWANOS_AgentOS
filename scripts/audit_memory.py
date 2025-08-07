#!/usr/bin/env python3
"""📄  scripts/audit_memory.py

모든 JSON 메모리 파일을 스캔하여
  • memory_inventory.csv (path·size·mtime·keys)
  • schema_report.md    (상위 Key 출현 빈도)
를 생성한다.
"""

import argparse, csv, json, sys
from pathlib import Path
from datetime import datetime
from collections import Counter


def scan_files(roots):
    rows, counter = [], Counter()
    for root in roots:
        for fp in Path(root).rglob("*.json"):
            try:
                obj = json.loads(fp.read_text(encoding="utf-8"))
                keys = set(obj.keys()) if isinstance(obj, dict) else {"__NONDICT__"}
                mtime = datetime.utcfromtimestamp(fp.stat().st_mtime).isoformat() + "Z"
                size = fp.stat().st_size
            except Exception as e:
                keys, mtime, size = {"__ERROR__"}, "ERROR", 0
                print(f"[warn] {fp}: {e}", file=sys.stderr)
            rows.append((str(fp), size, mtime, ";".join(sorted(keys))))
            counter.update(keys)
    return rows, counter


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--roots", nargs="*", default=["data/memory", "data/reflections"])
    p.add_argument("--outdir", default=".")
    args = p.parse_args()

    rows, counter = scan_files(args.roots)
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    (out / "memory_inventory.csv").write_text(
        "path,bytes,mtime,keys\n" +
        "\n".join(",".join(map(str, r)) for r in rows),
        encoding="utf-8"
    )
    (out / "schema_report.md").write_text(
        "# Memory Key Frequency\n\n" +
        "\n".join(f"- **{k}** : {v}" for k, v in counter.most_common()),
        encoding="utf-8"
    )
    print("✅  inventory & schema reports generated")


if __name__ == "__main__":
    main()
