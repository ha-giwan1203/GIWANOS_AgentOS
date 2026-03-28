#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 4 — 기준정보 매칭
기준정보 시트에서 품번별 단가·Usage 로딩 → GERP 품번과 매칭 → 미등록 품번 추출

단가 권위값: 기준정보 파일. GERP 자체 단가와 다를 수 있음.
RSP 모듈품번 역추적: E열(모듈품번) → C열(품번), C/E열만 사용 (별도 처리)

실행: python step4_기준정보매칭.py
입력: _cache/step2_gerp.json
출력: _cache/step4_matched.json
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from _pipeline_config import *
import pandas as pd
from datetime import datetime

print("=" * 60)
print("Step 4: 기준정보 매칭")
print("=" * 60)

# ── 의존 체크 ─────────────────────────────────────────────────
if not os.path.exists(CACHE_STEP2):
    print(f"[ERROR] Step2 결과 없음. step2_gerp처리.py 먼저 실행하세요.")
    sys.exit(1)
if not os.path.exists(MASTER_FILE):
    print(f"[ERROR] 기준정보 파일 없음: {MASTER_FILE}")
    sys.exit(1)

with open(CACHE_STEP2, encoding='utf-8') as f:
    step2 = json.load(f)

day_pivot   = step2['day_pivot']
night_pivot = step2['night_pivot']
all_gerp_pns = set()
for pv in [day_pivot, night_pivot]:
    for lc, d in pv.items():
        all_gerp_pns.update(d.keys())

# ── 기준정보 로딩 ─────────────────────────────────────────────
print(f"\n[1/3] 기준정보 로딩...")
xf = pd.ExcelFile(MASTER_FILE)
master = {}      # {라인코드: [{'part_no', 'price', 'usage', 'price_type', 'vtype'}, ...]}
master_pns = set()
mc = MASTER_COL

for lc in LINE_ORDER:
    if lc not in xf.sheet_names:
        print(f"  ⚠ [{lc}] 시트 없음")
        master[lc] = []
        continue

    df = pd.read_excel(xf, sheet_name=lc, header=None)
    data = df.iloc[3:].reset_index(drop=True)   # row 3+: 데이터

    rows = []
    for _, row in data.iterrows():
        pn    = str(row.iloc[mc['part_no']]).strip()   if pd.notna(row.iloc[mc['part_no']])    else ''
        vcode = str(row.iloc[mc['vendor_cd']]).strip() if pd.notna(row.iloc[mc['vendor_cd']])  else ''
        if not pn or pn == 'nan':
            continue
        if vcode != VENDOR_CODE:
            continue

        usage     = int(row.iloc[mc['usage']])     if pd.notna(row.iloc[mc['usage']])     else 1
        price_type= str(row.iloc[mc['price_type']]).strip() if pd.notna(row.iloc[mc['price_type']]) else ''
        vtype     = str(row.iloc[mc['vtype']]).strip()      if pd.notna(row.iloc[mc['vtype']])      else ''
        assy_part = str(row.iloc[mc['assy_part']]).strip() if pd.notna(row.iloc[mc['assy_part']]) else ''
        price_raw = row.iloc[mc['price']]
        try:
            price = float(price_raw)
        except (TypeError, ValueError):
            price = 0.0

        rows.append({
            'part_no':    pn,
            'assy_part':  assy_part,
            'price':      price,
            'usage':      usage,
            'price_type': price_type,
            'vtype':      vtype,
        })
        master_pns.add(pn)

    # 동일 품번+동일 단가 중복 제거 (다중 단가는 유지)
    seen = set()
    deduped = []
    dup_count = 0
    for r in rows:
        key = (r['part_no'], r['price'])
        if key in seen:
            dup_count += 1
            continue
        seen.add(key)
        deduped.append(r)
    if dup_count > 0:
        print(f"  ⚠ [{lc}] 동일품번-동일단가 중복 {dup_count}건 제거")
    rows = deduped

    master[lc] = rows
    priced = sum(1 for r in rows if r['price'] > 0)
    print(f"  {lc:10s}: {len(rows):>5d}행  단가있음:{priced}  미단가:{len(rows)-priced}")

# ── RSP 모듈품번 역추적 (별도) ───────────────────────────────
print(f"\n[2/3] RSP 모듈품번 역추적 (C/E열)...")
rsp_map = {}   # RSP품번 → 완성품 품번
for lc in LINE_ORDER:
    if lc not in xf.sheet_names:
        continue
    df = pd.read_excel(xf, sheet_name=lc, header=None)
    data = df.iloc[3:].reset_index(drop=True)
    if data.shape[1] < 5:
        continue
    for _, row in data.iterrows():
        pn_c = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ''   # C열: 품번
        pn_e = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ''   # E열: 모듈품번
        if pn_e.startswith('RSP') and pn_c and pn_c != 'nan':
            rsp_map[pn_e] = pn_c

print(f"  RSP 역추적 맵: {len(rsp_map)}건")

# ── 미등록 품번 추출 ──────────────────────────────────────────
print(f"\n[3/3] GERP 품번 vs 기준정보 매칭...")
unmatched = sorted(all_gerp_pns - master_pns - {'nan', 'None', ''})
matched_n  = len(all_gerp_pns - set(unmatched))
print(f"  GERP 전체품번: {len(all_gerp_pns)}개")
print(f"  매칭됨: {matched_n}개  미매핑: {len(unmatched)}개")
if unmatched:
    print(f"  미매핑 품번 (상위20): {unmatched[:20]}")

# ── JSON 저장 ─────────────────────────────────────────────────
result = {
    "step": 4,
    "timestamp": datetime.now().isoformat(),
    "master": master,
    "master_pn_count": len(master_pns),
    "gerp_pn_count": len(all_gerp_pns),
    "unmatched_gerp": unmatched,
    "rsp_map": rsp_map,
}

with open(CACHE_STEP4, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"\n저장: {CACHE_STEP4}")
print("Step 4 완료")
