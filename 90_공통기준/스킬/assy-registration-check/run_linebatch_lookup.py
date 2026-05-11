"""
24 모품번 ERP 라인배치 자동조회 진입점.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lookup_linebatch

CACHE_OUT = Path(r"C:\Users\User\Desktop\업무리스트\05_생산실적\조립비정산\05월\_cache\linebatch_24pns.json")

PNS_24 = [
    "7560241020", "88810BT000", "88810BT100", "88810BT200", "88810BT300",
    "88810NV000", "88810R6500", "88820BC000", "88820BN300",
    "88820BT000", "88820BT100", "88820BT200", "88820BT300",
    "88820GG500", "88820R6500", "89870AR500", "89870NV000", "89870R6500",
    "89880CV500", "89880NV000", "89880R6000", "89880R6500",
    "MO89870R6000", "MO89880R6000",
]

result = lookup_linebatch.lookup_colors_via_linebatch(PNS_24)
CACHE_OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
print(f"\n[DONE] cache → {CACHE_OUT}")

# 요약
print(f"\n결과 요약:")
n_found = sum(1 for v in result.values() if v)
n_empty = sum(1 for v in result.values() if not v)
print(f"  rows>0: {n_found} / rows=0: {n_empty}")
for pn, rows in result.items():
    if rows:
        prods = sorted({(r.get("PROD_NO") if isinstance(r, dict) else "") for r in rows if isinstance(r, dict)})
        print(f"  {pn}: {len(rows)}행 → {prods[:8]}")
    else:
        print(f"  {pn}: 0행")
