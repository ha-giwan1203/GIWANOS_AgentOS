"""1.XLS 매칭 결과를 cache JSON으로 export — merge_colors_v2가 통합 사용."""
import json
import re
import sys
from pathlib import Path
import xlrd

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

XLS = Path(r"C:\Users\User\Desktop\1.XLS")
OUT = Path(r"C:\Users\User\Desktop\업무리스트\05_생산실적\조립비정산\05월\_cache\xls1_colors.json")

TARGETS = [
    "7560241020", "88810BT000", "88810BT100", "88810BT200", "88810BT300",
    "88810NV000", "88810R6500", "88820BC000", "88820BN300",
    "88820BT000", "88820BT100", "88820BT200", "88820BT300",
    "88820GG500", "88820R6500", "89870AR500", "89870NV000", "89870R6500",
    "89880CV500", "89880NV000", "89880R6000", "89880R6500",
    "MO89870R6000", "MO89880R6000",
    "88820T1500", "88820JI500", "89870BT000", "89880BT000",
    "89870BP100", "89880BP100", "88810T1500", "88810JI500",
]

wb = xlrd.open_workbook(str(XLS), encoding_override="cp949")
ws = wb.sheet_by_index(0)

pat = re.compile(r"^(MO|MV|W|X|Z)?[0-9A-Z]{8,15}$")
col_scores = {c: sum(1 for r in range(1, min(100, ws.nrows))
                     if ws.cell_value(r, c) and isinstance(ws.cell_value(r, c), str)
                     and pat.match(ws.cell_value(r, c)))
              for c in range(ws.ncols)}
pn_col = max(col_scores, key=col_scores.get)

# 매칭 결과 → {모품번: [PROD_NO,...]}
out = {}
seen = {t: set() for t in TARGETS}
for r in range(1, ws.nrows):
    v = ws.cell_value(r, pn_col)
    if not v: continue
    s = str(v).strip()
    for t in TARGETS:
        if (s == t or s.startswith(t)) and s not in seen[t]:
            seen[t].add(s)
            out.setdefault(t, []).append(s)
            break

# 라인배치 cache 형식과 통일 — rows = [{PROD_NO: ...}, ...]
final = {}
for pn, prods in out.items():
    final[pn] = [{"PROD_NO": p} for p in sorted(prods)]

OUT.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"export: {OUT}")
print(f"매칭 모품번: {len(final)} / 총 PROD_NO: {sum(len(v) for v in final.values())}")
