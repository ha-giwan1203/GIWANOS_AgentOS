from __future__ import annotations

import glob
import json

from modules.report_paths import ROOT
LOGS = ROOT / r"data\logs"
LOGS.mkdir(parents=True, exist_ok=True)


def main():
    # 규칙: data\logs\api_calls\*.jsonl 안의 각 줄에 {"cost": float}가 있다고 가정
    src_dir = LOGS / "api_calls"
    total = 0.0
    entries = 0
    if src_dir.exists():
        for fn in glob.glob(str(src_dir / "*.jsonl")):
            with open(fn, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        total += float(obj.get("cost", 0))
                        entries += 1
                    except Exception:
                        pass
    out = {"entries": entries, "total_cost": round(total, 6)}
    (LOGS / "api_cost_log.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[OK] api_cost_log.json 갱신: entries={entries}, total={out['total_cost']}")


if __name__ == "__main__":
    main()

