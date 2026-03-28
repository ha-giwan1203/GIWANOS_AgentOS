#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 3 — 구ERP 처리
0109 필터 → LOT B 야간 분리 → 품번-수량 피벗 → JSON 출력

구ERP 주야 판정:
  - LOT NO 끝자리 B = 야간
  - A, S, C, R 등 나머지 전부 = 주간
구ERP SD9 집계: 업체코드 0109 전체 품번, 라인코드 무시

실행: python step3_구erp처리.py
출력: _cache/step3_olderp.json
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from _pipeline_config import *
import pandas as pd
from datetime import datetime

print("=" * 60)
print("Step 3: 구ERP 처리")
print("=" * 60)

if not os.path.exists(OLDERP_FILE):
    print(f"[ERROR] 구ERP 파일 없음: {OLDERP_FILE}")
    sys.exit(1)

# ── 로딩 ──────────────────────────────────────────────────────
print(f"\n[1/3] 구ERP 파일 로딩 (Sheet1)...")
df_raw = pd.read_excel(OLDERP_FILE, sheet_name='Sheet1', header=None)
data = df_raw.iloc[2:].reset_index(drop=True)

c = OLDERP_COL
all_data = pd.DataFrame({
    'vendor':    data.iloc[:, c['vendor']].astype(str).str.strip(),
    'part_no':   data.iloc[:, c['part_no']].astype(str).str.strip(),
    'qty':       pd.to_numeric(data.iloc[:, c['qty']], errors='coerce').fillna(0).astype(int),
    'line_code': data.iloc[:, c['line_code']].astype(str).str.strip(),
    'lot_no':    data.iloc[:, c['lot_no']].astype(str).str.strip(),
    'unit_cost': pd.to_numeric(data.iloc[:, c['unit_cost']], errors='coerce').fillna(0),
    'amount':    pd.to_numeric(data.iloc[:, c['amount']], errors='coerce').fillna(0),
})

print(f"  구ERP 전체: {len(all_data):,}행")

# ── 주야 분류 (전체 기준, LOTNO 끝자리) ───────────────────────
all_data['shift_type'] = all_data['lot_no'].apply(
    lambda x: '야간' if str(x).strip().endswith('B') else '주간'
)

# ── 0109 필터 ─────────────────────────────────────────────────
print(f"\n[2/3] 대원테크({VENDOR_CODE}) 필터링 및 라인 분석...")
erp_dw = all_data[all_data['vendor'].str.contains(VENDOR_CODE, na=False)].copy()
erp_dw['gerp_line'] = erp_dw['line_code'].map(OLD_ERP_LINE_MAP)
print(f"  대원테크: {len(erp_dw):,}행")

for lc_code in erp_dw['line_code'].dropna().unique():
    sub    = erp_dw[erp_dw['line_code'] == lc_code]
    mapped = OLD_ERP_LINE_MAP.get(lc_code, '(미매핑)')
    day_q  = sub[sub['shift_type'] == '주간']['qty'].sum()
    night_q= sub[sub['shift_type'] == '야간']['qty'].sum()
    print(f"  {lc_code:8s} → {mapped:10s}: 주간 {day_q:>8,}  야간 {night_q:>8,}")

# ── 피벗 생성 ─────────────────────────────────────────────────
print(f"\n[3/3] 품번 피벗 생성...")

# 전 업체 (SUB 라인 구ERP 수량 매칭용)
all_day_pv   = all_data[all_data['shift_type'] == '주간'].groupby('part_no')['qty'].sum().astype(int).to_dict()
all_night_pv = all_data[all_data['shift_type'] == '야간'].groupby('part_no')['qty'].sum().astype(int).to_dict()
all_total_pv = all_data.groupby('part_no')['qty'].sum().astype(int).to_dict()

# 대원테크 GERP 라인별 피벗 (SD9A01, SP3M3 — 라인코드 기반)
line_day_pv   = {}
line_night_pv = {}
line_total_pv = {}   # 주간+야간 합산 (SD9A01/SP3M3 비교용 총수량)
for gerp_lc in ['SD9A01', 'SP3M3']:
    sub = erp_dw[erp_dw['gerp_line'] == gerp_lc]
    if len(sub) == 0:
        continue
    d = sub[sub['shift_type'] == '주간'].groupby('part_no')['qty'].sum().astype(int).to_dict()
    n = sub[sub['shift_type'] == '야간'].groupby('part_no')['qty'].sum().astype(int).to_dict()
    t = sub.groupby('part_no')['qty'].sum().astype(int).to_dict()   # 총수량 합산
    if d:
        line_day_pv[gerp_lc]   = d
    if n:
        line_night_pv[gerp_lc] = n
    if t:
        line_total_pv[gerp_lc] = t
    print(f"  {gerp_lc:10s}: 주간품번 {len(d):>4}개  야간품번 {len(n):>4}개  총품번 {len(t):>4}개")

print(f"  전체업체 주간품번 {len(all_day_pv):,}개  야간품번 {len(all_night_pv):,}개")

# ── JSON 저장 ─────────────────────────────────────────────────
result = {
    "step": 3,
    "timestamp": datetime.now().isoformat(),
    "total_rows_all":  len(all_data),
    "total_rows_0109": len(erp_dw),
    # 대원테크 라인별 (SD9A01, SP3M3)
    "line_day_pivot":   line_day_pv,
    "line_night_pivot": line_night_pv,
    "line_total_pivot": line_total_pv,   # 주간+야간 합산 총수량 (SD9A01/SP3M3 비교 기준)
    # 전 업체 합산 (SUB 라인 매칭용)
    "all_day_pivot":   all_day_pv,
    "all_night_pivot": all_night_pv,
    "all_total_pivot": all_total_pv,
}

with open(CACHE_STEP3, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"\n저장: {CACHE_STEP3}")
print("Step 3 완료")
