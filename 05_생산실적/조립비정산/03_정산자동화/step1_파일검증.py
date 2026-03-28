#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 1 — 파일검증
입력파일(GERP, 구ERP, 기준정보) 존재여부 · 시트구조 · 헤더 검증

실행: python step1_파일검증.py
출력: _cache/step1_validation.json
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from _pipeline_config import *
import pandas as pd
from datetime import datetime

print("=" * 60)
print("Step 1: 파일 검증")
print("=" * 60)

results = {
    "step": 1,
    "timestamp": datetime.now().isoformat(),
    "status": "OK",
    "checks": [],
    "files": {
        "master": MASTER_FILE,
        "gerp":   GERP_FILE,
        "olderp": OLDERP_FILE,
    }
}

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    msg = f"  [{status}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    results["checks"].append({"name": name, "status": status, "detail": detail})
    if not condition:
        results["status"] = "FAIL"


# ── 1. 파일 존재 여부 ──────────────────────────────────────────
print("\n[파일 존재 여부]")
check("기준정보 파일 존재", os.path.exists(MASTER_FILE), MASTER_FILE)
check("GERP 파일 존재",    os.path.exists(GERP_FILE),   GERP_FILE)
check("구ERP 파일 존재",   os.path.exists(OLDERP_FILE), OLDERP_FILE)

# ── 2. 기준정보 시트 구조 ──────────────────────────────────────
print("\n[기준정보 시트 구조]")
if os.path.exists(MASTER_FILE):
    try:
        xf = pd.ExcelFile(MASTER_FILE)
        sheets = xf.sheet_names
        missing_lines = [lc for lc in LINE_ORDER if lc not in sheets]
        check("기준정보 라인 시트 10개 존재", len(missing_lines) == 0,
              f"누락={missing_lines}" if missing_lines else f"전체:{sheets[:10]}")

        # 각 라인 시트 row3+ 데이터 유무 확인
        for lc in LINE_ORDER:
            if lc not in sheets:
                continue
            df = pd.read_excel(xf, sheet_name=lc, header=None)
            data_rows = len(df) - 3   # row 0~2: 제목/헤더, row 3+: 데이터
            has_data = data_rows > 0
            check(f"  기준정보 [{lc}] 데이터행", has_data, f"{data_rows}행")
    except Exception as e:
        check("기준정보 파일 열기", False, str(e))
else:
    print("  [SKIP] 기준정보 파일 없음")

# ── 3. GERP 시트 구조 ─────────────────────────────────────────
print("\n[GERP 파일 구조]")
if os.path.exists(GERP_FILE):
    try:
        df = pd.read_excel(GERP_FILE, sheet_name=0, header=None, nrows=5)
        check("GERP 시트 열기", True, f"{df.shape[1]}열")

        # col20=vendor_cd 존재 확인
        check("GERP 컬럼수 최소 21개", df.shape[1] >= 21, f"실제 {df.shape[1]}열")

        # 데이터 행수 확인
        df_full = pd.read_excel(GERP_FILE, sheet_name=0, header=None)
        data_rows = len(df_full) - 2
        check("GERP 데이터행 1건 이상", data_rows > 0, f"{data_rows:,}행")

        # 주야구분 값 확인
        col_shift = df_full.iloc[2:, GERP_COL['shift']].astype(str).str.strip()
        valid_shifts = set(col_shift.dropna().unique())
        check("GERP 주야구분 값 (정상/추가 포함)",
              '정상' in valid_shifts or '추가' in valid_shifts,
              f"발견값={sorted(valid_shifts)[:10]}")

        # 대원테크 데이터 존재 확인
        col_vendor = df_full.iloc[2:, GERP_COL['vendor_cd']].astype(str).str.strip()
        dw_count = (col_vendor == VENDOR_CODE).sum()
        check(f"GERP 대원테크({VENDOR_CODE}) 데이터 존재", dw_count > 0, f"{dw_count:,}행")

    except Exception as e:
        check("GERP 파일 열기", False, str(e))
else:
    print("  [SKIP] GERP 파일 없음")

# ── 4. 구ERP 시트 구조 ────────────────────────────────────────
print("\n[구ERP 파일 구조]")
if os.path.exists(OLDERP_FILE):
    try:
        xf = pd.ExcelFile(OLDERP_FILE)
        check("구ERP Sheet1 존재", 'Sheet1' in xf.sheet_names,
              f"시트목록={xf.sheet_names[:5]}")

        if 'Sheet1' in xf.sheet_names:
            df = pd.read_excel(xf, sheet_name='Sheet1', header=None)
            data_rows = len(df) - 2
            check("구ERP 데이터행 1건 이상", data_rows > 0, f"{data_rows:,}행")
            check("구ERP 컬럼수 최소 13개", df.shape[1] >= 13, f"실제 {df.shape[1]}열")

            col_lot = df.iloc[2:, OLDERP_COL['lot_no']].astype(str).str.strip()
            lot_vals = set(col_lot.dropna().str[-1].unique())
            check("구ERP LOTNO 끝자리 B/A/S/C 포함",
                  len(lot_vals & {'A', 'B', 'C', 'S'}) > 0,
                  f"끝자리값={sorted(lot_vals)[:10]}")

            col_vendor = df.iloc[2:, OLDERP_COL['vendor']].astype(str).str.strip()
            dw_count = col_vendor.str.contains(VENDOR_CODE, na=False).sum()
            check(f"구ERP 대원테크({VENDOR_CODE}) 데이터 존재", dw_count > 0, f"{dw_count:,}행")

    except Exception as e:
        check("구ERP 파일 열기", False, str(e))
else:
    print("  [SKIP] 구ERP 파일 없음")

# ── 결과 저장 ─────────────────────────────────────────────────
with open(CACHE_STEP1, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

pass_n = sum(1 for c in results['checks'] if c['status'] == 'PASS')
fail_n = sum(1 for c in results['checks'] if c['status'] == 'FAIL')

print(f"\n{'='*60}")
print(f"결과: {results['status']}  (PASS {pass_n} / FAIL {fail_n})")
print(f"저장: {CACHE_STEP1}")
if results['status'] == 'FAIL':
    print("⚠ FAIL 항목 해결 후 다음 Step 진행 권장")
