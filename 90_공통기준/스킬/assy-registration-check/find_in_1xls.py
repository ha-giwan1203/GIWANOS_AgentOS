"""1.XLS 7202행에서 미등록 32 모품번 매칭."""
import sys
from pathlib import Path
import xlrd

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

XLS = Path(r"C:\Users\User\Desktop\1.XLS")

# 미등록 32 모품번 (W접두사 제외)
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
print(f"1.XLS: {ws.nrows}행 x {ws.ncols}컬럼")

# PROD_NO 컬럼 자동 감지 (영문+숫자 패턴 가장 많은 컬럼)
import re
pat = re.compile(r"^(MO|MV|W|X|Z)?[0-9A-Z]{8,15}$")
col_scores = {}
for c in range(ws.ncols):
    cnt = 0
    for r in range(1, min(100, ws.nrows)):
        v = ws.cell_value(r, c)
        if v and isinstance(v, str) and pat.match(v):
            cnt += 1
    col_scores[c] = cnt
pn_col = max(col_scores, key=col_scores.get)
print(f"PROD_NO 추정 컬럼: col {pn_col} (매칭 {col_scores[pn_col]}건)")

# 매칭
hits = {t: [] for t in TARGETS}
for r in range(1, ws.nrows):
    v = ws.cell_value(r, pn_col)
    if not v: continue
    s = str(v).strip()
    for t in TARGETS:
        # 정확 일치 또는 prefix LIKE
        if s == t or s.startswith(t):
            hits[t].append((r, s))
            break

print(f"\n=== 매칭 결과 ===")
n_hit = 0
for t in TARGETS:
    if hits[t]:
        n_hit += 1
        unique_pns = sorted({s for _, s in hits[t]})
        print(f"  {t}: {len(hits[t])}행 → unique PROD_NO {len(unique_pns)}")
        for pn in unique_pns[:10]:
            print(f"     {pn}")
    else:
        print(f"  {t}: 0건")
print(f"\n매칭 모품번: {n_hit}/{len(TARGETS)}")
