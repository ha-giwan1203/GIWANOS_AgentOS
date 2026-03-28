#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
스모크 테스트 3: 품번 불일치 시 Step 4에서 경고 확인

시나리오:
  - GERP에 'DUMMY-UNKNOWN-999' 품번 포함
  - 기준정보에는 해당 품번 없음
  - Step 2 실행 → GERP 피벗에 DUMMY-UNKNOWN-999 포함 확인
  - Step 4 실행 → unmatched_gerp에 DUMMY-UNKNOWN-999 포함 확인
  - (선택) Step 5, 6 실행 → Step 6의 INFO 항목 6 확인

추가 시나리오:
  - GERP에만 존재하고 기준정보에 없는 품번 여러 개 처리
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

UNKNOWN_PART = 'DUMMY-UNKNOWN-999'
KNOWN_PART   = 'TST-001'

print("=" * 55)
print("test_unmatched_parts: 품번 불일치 → Step4 경고 확인")
print("=" * 55)

with tempfile.TemporaryDirectory() as tmp_dir:
    cache_dir = os.path.join(tmp_dir, '_cache')
    os.makedirs(cache_dir, exist_ok=True)

    gerp_path   = os.path.join(tmp_dir, 'gerp.xlsx')
    olderp_path = os.path.join(tmp_dir, 'olderp.xlsx')
    master_path = os.path.join(tmp_dir, 'master.xlsx')

    # ── 더미 파일 생성 ──────────────────────────────────────────
    section("더미 입력 파일 생성")

    # GERP: 알려진 품번 + 알려지지 않은 품번
    make_gerp(gerp_path, rows=[
        # 기준정보에 있는 품번
        dict(line='SD9A01', product_no=KNOWN_PART, usage=1,
             shift='정상', qty=100, unit_price=300, amount=30000, vendor_cd='0109'),
        # 기준정보에 없는 품번
        dict(line='SD9A01', product_no=UNKNOWN_PART, usage=1,
             shift='정상', qty=50, unit_price=999, amount=49950, vendor_cd='0109'),
        dict(line='SP3M3',  product_no='TST-SP3-001', usage=1,
             shift='정상', qty=200, unit_price=120, amount=24000, vendor_cd='0109'),
    ])
    print(f"  GERP: {gerp_path}  (포함: {UNKNOWN_PART})")

    # 구ERP: UNKNOWN 품번 없음
    make_olderp(olderp_path, rows=[
        dict(vendor='0109', part_no=KNOWN_PART, qty=95, line_code='TD9',
             lot_no='2026-01A', unit_cost=300, amount=28500),
        dict(vendor='0109', part_no='TST-SP3-001', qty=195, line_code='SP3S03',
             lot_no='2026-01A', unit_cost=120, amount=23400),
    ])

    # 기준정보: KNOWN_PART만 등록, UNKNOWN_PART 미등록
    make_master(master_path, rows_per_line={
        'SD9A01': [
            dict(part_no=KNOWN_PART, vendor_cd='0109', line_code='SD9A01',
                 assy_part='', usage=1, price_type='기준', price=300.0, vtype='SD9'),
            # UNKNOWN_PART 없음 (의도적 누락)
        ],
        'SP3M3': [
            dict(part_no='TST-SP3-001', vendor_cd='0109', line_code='SP3M3',
                 assy_part='', usage=1, price_type='기준', price=120.0, vtype='SP3'),
        ],
    })
    print(f"  기준정보: {master_path}  ({UNKNOWN_PART} 미등록)")

    with patch_config(tmp_dir, month='01'):

        # ── Step 2 실행 ─────────────────────────────────────────
        section("Step 2: GERP 처리")

        cache2 = os.path.join(cache_dir, 'step2_gerp.json')
        ret2 = run_step('step2_gerp처리.py', cache2)
        print(ret2['stdout'])
        assert_or_fail(ret2['exit_code'] == 0, "Step2 exit code = 0")

        s2 = ret2['result']
        assert_or_fail(s2 is not None, "step2_gerp.json 생성")

        # GERP 피벗에 UNKNOWN 품번 포함 확인
        sd9_day = s2.get('day_pivot', {}).get('SD9A01', {})
        assert_or_fail(
            UNKNOWN_PART in sd9_day,
            f"step2 day_pivot SD9A01에 '{UNKNOWN_PART}' 포함",
        )
        assert_or_fail(
            KNOWN_PART in sd9_day,
            f"step2 day_pivot SD9A01에 '{KNOWN_PART}' 포함",
        )

        # ── Step 3 실행 ─────────────────────────────────────────
        section("Step 3: 구ERP 처리")

        cache3 = os.path.join(cache_dir, 'step3_olderp.json')
        ret3 = run_step('step3_구erp처리.py', cache3)
        assert_or_fail(ret3['exit_code'] == 0, "Step3 exit code = 0")

        # ── Step 4 실행 ─────────────────────────────────────────
        section("Step 4: 기준정보 매칭")

        cache4 = os.path.join(cache_dir, 'step4_matched.json')
        ret4 = run_step('step4_기준정보매칭.py', cache4)
        print(ret4['stdout'])
        assert_or_fail(ret4['exit_code'] == 0, "Step4 exit code = 0")

        s4 = ret4['result']
        assert_or_fail(s4 is not None, "step4_matched.json 생성")

        # unmatched_gerp에 UNKNOWN 품번 포함 확인
        unmatched = s4.get('unmatched_gerp', [])
        assert_or_fail(
            UNKNOWN_PART in unmatched,
            f"unmatched_gerp에 '{UNKNOWN_PART}' 포함 (실제: {unmatched})",
        )
        assert_or_fail(
            KNOWN_PART not in unmatched,
            f"unmatched_gerp에 '{KNOWN_PART}' 미포함 (알려진 품번은 매칭됨)",
        )
        print(f"  unmatched_gerp: {unmatched}")

        # master에는 KNOWN_PART만 있음
        sd9_master = s4.get('master', {}).get('SD9A01', [])
        master_pns = [r['part_no'] for r in sd9_master]
        assert_or_fail(
            KNOWN_PART in master_pns,
            f"master SD9A01에 '{KNOWN_PART}' 존재",
        )
        assert_or_fail(
            UNKNOWN_PART not in master_pns,
            f"master SD9A01에 '{UNKNOWN_PART}' 없음",
        )

        # ── Step 5 실행 ─────────────────────────────────────────
        section("Step 5: 정산 계산")

        cache5 = os.path.join(cache_dir, 'step5_settlement.json')
        ret5 = run_step('step5_정산계산.py', cache5)
        assert_or_fail(ret5['exit_code'] == 0, "Step5 exit code = 0")

        s5 = ret5['result']
        # unmatched_gerp는 Step5 JSON에도 전달됨
        assert_or_fail(
            UNKNOWN_PART in s5.get('unmatched_gerp', []),
            f"step5_settlement.json의 unmatched_gerp에 '{UNKNOWN_PART}' 포함",
        )

        # UNKNOWN 품번은 기준정보 없으므로 items에 없어야 함
        sd9_items = s5['lines'].get('SD9A01', {}).get('items', [])
        item_pns = [r['part_no'] for r in sd9_items]
        assert_or_fail(
            UNKNOWN_PART not in item_pns,
            f"Step5 SD9A01 items에 '{UNKNOWN_PART}' 없음 (기준정보 없어 계산 제외)",
        )

        # ── Step 6 실행 ─────────────────────────────────────────
        section("Step 6: 검증 (미매핑 INFO 확인)")

        cache6 = os.path.join(cache_dir, 'step6_validation.json')
        ret6 = run_step('step6_검증.py', cache6)
        print(ret6['stdout'])
        assert_or_fail(ret6['exit_code'] == 0, "Step6 exit code = 0")

        s6 = ret6['result']
        # 미매핑 품번 존재 → 항목 6은 INFO
        check6 = next((c for c in s6['checks'] if c['no'] == 6), None)
        assert_or_fail(check6 is not None, "Step6 항목 6 (미매핑 품번 현황) 존재")
        assert_or_fail(
            check6['status'] == 'INFO',
            f"항목 6 status={check6['status']} (기대: INFO — 미매핑 존재)",
        )
        assert_or_fail(
            UNKNOWN_PART in check6['detail'] or str(len(unmatched)) in check6['detail'],
            f"항목 6 detail에 미매핑 정보 포함: {check6['detail']}",
        )
        print(f"  항목 6 detail: {check6['detail']}")

        # 미매핑이 있어도 FAIL 항목 없으면 overall PASS
        assert_or_fail(
            s6['fail'] == 0,
            f"FAIL 건수={s6['fail']} (기대: 0 — 미매핑은 INFO, FAIL 아님)",
        )

print("\n" + "=" * 55)
print("test_unmatched_parts: ALL PASS")
print("=" * 55)
