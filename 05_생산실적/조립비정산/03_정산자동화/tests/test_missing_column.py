#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
스모크 테스트 2: 필수 컬럼 누락 시 Step 1에서 FAIL 확인

시나리오:
  - GERP 파일을 컬럼 10개(< 21)로 생성
  - Step 1 실행 → step1_validation.json
  - 기대: status = "FAIL", "GERP 컬럼수 최소 21개" 항목이 FAIL

추가 검증:
  - GERP 컬럼이 충분해도 구ERP Sheet1 없으면 해당 항목 FAIL 확인
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from _test_helpers import (
    patch_config, make_gerp, make_olderp, make_master,
    run_step, assert_or_fail, section, PIPELINE_DIR,
)

import openpyxl

print("=" * 55)
print("test_missing_column: 필수 컬럼 누락 → Step1 FAIL 확인")
print("=" * 55)

# ── 시나리오 A: GERP 컬럼 10개 (< 21) ─────────────────────────
section("시나리오 A: GERP 컬럼 부족 (ncols=10)")

with tempfile.TemporaryDirectory() as tmp_dir:
    cache_dir = os.path.join(tmp_dir, '_cache')
    os.makedirs(cache_dir, exist_ok=True)

    gerp_path   = os.path.join(tmp_dir, 'gerp.xlsx')
    olderp_path = os.path.join(tmp_dir, 'olderp.xlsx')
    master_path = os.path.join(tmp_dir, 'master.xlsx')

    # GERP: 컬럼 10개 (최소 요구 21개 미충족)
    make_gerp(gerp_path, rows=[
        dict(line='SD9A01', product_no='TST-001', usage=1,
             shift='정상', qty=100, unit_price=300, amount=30000, vendor_cd='0109'),
    ], ncols=10)
    make_olderp(olderp_path)
    make_master(master_path)

    with patch_config(tmp_dir, month='01'):
        cache_path = os.path.join(cache_dir, 'step1_validation.json')
        ret = run_step('step1_파일검증.py', cache_path)

        print(ret['stdout'])

        # Step 1은 sys.exit 없이 실행 완료 (exit code 0이어도 status FAIL)
        assert_or_fail(
            ret['exit_code'] == 0,
            f"Step1 exit code={ret['exit_code']} (Step1은 FAIL이어도 exit 0)",
        )

        s1 = ret['result']
        assert_or_fail(s1 is not None, "step1_validation.json 생성 확인")
        assert_or_fail(
            s1['status'] == 'FAIL',
            f"status={s1['status']} (기대: FAIL — 컬럼 부족)",
        )

        # "GERP 컬럼수 최소 21개" 항목 확인
        col_check = next(
            (c for c in s1['checks'] if 'GERP 컬럼수' in c['name']),
            None
        )
        assert_or_fail(col_check is not None, "'GERP 컬럼수' 항목 존재")
        assert_or_fail(
            col_check['status'] == 'FAIL',
            f"'GERP 컬럼수' status={col_check['status']} (기대: FAIL)",
        )
        print(f"  detail: {col_check['detail']}")

# ── 시나리오 B: 구ERP Sheet1 없음 ─────────────────────────────
section("시나리오 B: 구ERP Sheet1 없음 (시트명 틀림)")

with tempfile.TemporaryDirectory() as tmp_dir:
    cache_dir = os.path.join(tmp_dir, '_cache')
    os.makedirs(cache_dir, exist_ok=True)

    gerp_path   = os.path.join(tmp_dir, 'gerp.xlsx')
    olderp_path = os.path.join(tmp_dir, 'olderp.xlsx')
    master_path = os.path.join(tmp_dir, 'master.xlsx')

    # 정상 GERP
    make_gerp(gerp_path)

    # 구ERP: Sheet1 대신 잘못된 시트명 사용
    wb = openpyxl.Workbook()
    wb.active.title = 'Data'          # 'Sheet1' 아닌 이름
    wb.active.append(['HEADER'] * 13)
    wb.active.append(['HEADER'] * 13)
    wb.active.append(['0109', None, None, None, 'TST-001', 100, None, 'TD9', None, None, 'xxxA', 300, 30000])
    wb.save(olderp_path)

    make_master(master_path)

    with patch_config(tmp_dir, month='01'):
        cache_path = os.path.join(cache_dir, 'step1_validation.json')
        ret = run_step('step1_파일검증.py', cache_path)

        print(ret['stdout'])

        s1 = ret['result']
        assert_or_fail(s1 is not None, "step1_validation.json 생성 확인")
        assert_or_fail(
            s1['status'] == 'FAIL',
            f"status={s1['status']} (기대: FAIL — Sheet1 없음)",
        )

        sheet_check = next(
            (c for c in s1['checks'] if 'Sheet1' in c['name']),
            None
        )
        assert_or_fail(sheet_check is not None, "'Sheet1' 항목 존재")
        assert_or_fail(
            sheet_check['status'] == 'FAIL',
            f"'Sheet1' status={sheet_check['status']} (기대: FAIL)",
        )
        print(f"  detail: {sheet_check['detail']}")

# ── 시나리오 C: 기준정보 라인 시트 누락 ───────────────────────
section("시나리오 C: 기준정보 시트 일부 누락 (SD9A01만 존재)")

with tempfile.TemporaryDirectory() as tmp_dir:
    cache_dir = os.path.join(tmp_dir, '_cache')
    os.makedirs(cache_dir, exist_ok=True)

    gerp_path   = os.path.join(tmp_dir, 'gerp.xlsx')
    olderp_path = os.path.join(tmp_dir, 'olderp.xlsx')
    master_path = os.path.join(tmp_dir, 'master.xlsx')

    make_gerp(gerp_path)
    make_olderp(olderp_path)

    # 기준정보: SD9A01 시트만 존재 (나머지 9개 없음)
    wb = openpyxl.Workbook()
    wb.active.title = 'SD9A01'
    for _ in range(3):
        wb.active.append(['HEADER'] * 8)
    wb.active.append(['TST-001', '0109', 'SD9A01', '', 1, '기준', 300.0, 'SD9'])
    wb.save(master_path)

    with patch_config(tmp_dir, month='01'):
        cache_path = os.path.join(cache_dir, 'step1_validation.json')
        ret = run_step('step1_파일검증.py', cache_path)

        s1 = ret['result']
        assert_or_fail(s1 is not None, "step1_validation.json 생성 확인")
        assert_or_fail(
            s1['status'] == 'FAIL',
            f"status={s1['status']} (기대: FAIL — 라인 시트 누락)",
        )

        sheet10_check = next(
            (c for c in s1['checks'] if '라인 시트 10개' in c['name']),
            None
        )
        assert_or_fail(sheet10_check is not None, "'라인 시트 10개' 항목 존재")
        assert_or_fail(
            sheet10_check['status'] == 'FAIL',
            f"'라인 시트 10개' status={sheet10_check['status']} (기대: FAIL)",
        )
        print(f"  detail: {sheet10_check['detail']}")

print("\n" + "=" * 55)
print("test_missing_column: ALL PASS")
print("=" * 55)
