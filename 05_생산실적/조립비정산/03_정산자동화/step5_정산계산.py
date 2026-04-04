#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 5 — 정산 계산
라인별 금액 계산 → JSON 저장 (Step7 엑셀 생성용 중간 데이터)

계산 규칙 (CLAUDE.md 기준):
  - 총 정산금액 = (총수량 × 단가) + (야간수량 × 단가 × 30%)
  - SP3M3 야간: qty × 170원 고정단가 (야간 기본단가 30% 적용 없음)
  - SD9A01 단가기준판정: 단가 ≤ 500 → 야간가산, > 500 → 기본
  - Usage=2 품번: 수량 2배 환산

실행: python step5_정산계산.py
입력: _cache/step2_gerp.json, _cache/step3_olderp.json, _cache/step4_matched.json
출력: _cache/step5_settlement.json
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from _pipeline_config import *
from datetime import datetime

print("=" * 60)
print("Step 5: 정산 계산")
print("=" * 60)

# ── 의존 체크 ─────────────────────────────────────────────────
for fpath, name in [(CACHE_STEP2, 'Step2'), (CACHE_STEP3, 'Step3'), (CACHE_STEP4, 'Step4')]:
    if not os.path.exists(fpath):
        print(f"[ERROR] {name} 결과 없음: {fpath}")
        sys.exit(1)

with open(CACHE_STEP2, encoding='utf-8') as f:
    step2 = json.load(f)
with open(CACHE_STEP3, encoding='utf-8') as f:
    step3 = json.load(f)
with open(CACHE_STEP4, encoding='utf-8') as f:
    step4 = json.load(f)

master      = step4['master']
day_pivot   = step2['day_pivot']
night_pivot = step2['night_pivot']
day_amt_pivot   = step2.get('day_amt_pivot', {})
night_amt_pivot = step2.get('night_amt_pivot', {})
gerp_assy_lookup = step2.get('gerp_assy_lookup', {})
# 구ERP 피벗: OUTER/MAIN은 라인별, SUB는 전체업체 합산
olderp_line_day   = step3['line_day_pivot']
olderp_line_night = step3['line_night_pivot']
olderp_line_total = step3.get('line_total_pivot', {})   # 주간+야간 합산 총수량
olderp_all_day    = step3['all_day_pivot']
olderp_all_night  = step3['all_night_pivot']
olderp_all_total  = step3['all_total_pivot']
# 대원테크 0109 전체 — 라인코드 무시 (SD9A01 집계용)
olderp_dw_day     = step3.get('dw_day_pivot', {})
olderp_dw_night   = step3.get('dw_night_pivot', {})
olderp_dw_total   = step3.get('dw_total_pivot', {})
support_detail    = step3.get('support_detail', {})


def get_olderp_pv(lc):
    """라인 유형별 구ERP 피벗 반환 — (day, night, total)"""
    li = LINE_INFO.get(lc, {})
    if lc == 'SD9A01':
        # SD9A01: 전체업체 피벗 (다른 업체 지원 물량 포함)
        return olderp_all_day, olderp_all_night, olderp_all_total
    elif lc == 'SP3M3':
        # SP3M3: 구ERP가 모듈품번(MO)으로만 집계 → 전체업체 피벗 사용
        return olderp_all_day, olderp_all_night, olderp_all_total
    else:
        # SUB 라인: 전 업체 합산 피벗 사용
        return olderp_all_day, olderp_all_night, olderp_all_total


def calc_night_price(lc, price, night_qty):
    """야간 정산금액 계산 (구ERP 방식 통일)

    SP3M3: qty × 170원 고정단가
    SD9A01: qty × 단가 × 1.3 (기본100% + 가산30%)
    기타 야간 없는 라인: 0
    """
    if night_qty == 0:
        return 0
    if lc == 'SP3M3':
        return night_qty * SP3M3_NIGHT_PRICE
    if lc == 'SD9A01':
        return round(night_qty * price * 1.3)
    return 0


def sd9_price_judgment(lc, price, night_qty):
    """SD9A01 단가기준판정 반환 (야간실적 없으면 None)"""
    if lc != 'SD9A01':
        return None
    if night_qty == 0:
        return None
    return '야간가산' if price <= 500 else '기본'


# ── 라인별 계산 ───────────────────────────────────────────────
print(f"\n라인별 정산 계산...")
lines_result = {}
summary_rows = []

for lc in LINE_ORDER:
    rows  = master.get(lc, [])
    gp_d  = day_pivot.get(lc, {})
    gp_n  = night_pivot.get(lc, {})
    gp_d_amt = day_amt_pivot.get(lc, {})
    gp_n_amt = night_amt_pivot.get(lc, {})
    ep_d, ep_n, ep_t = get_olderp_pv(lc)
    has_night  = LINE_INFO[lc]['has_night']

    # SP3M3 야간: RSP→기본품번(10자리)으로 변환됨
    # 같은 기본품번의 첫 품번에만 야간수량 할당, 나머지 0
    _sp3m3_ngt_used = set()  # 이미 할당된 기본품번 추적

    detail = []
    total_gerp_day_qty = total_gerp_day_amt = 0
    total_gerp_ngt_qty = total_gerp_ngt_amt = 0
    total_erp_day_qty  = total_erp_day_amt  = 0
    total_erp_ngt_qty  = total_erp_ngt_amt  = 0

    for r in rows:
        pn    = r['part_no']
        price = r['price']
        usage = r['usage']

        # GERP 수량 (Usage 환산)
        g_day_raw = gp_d.get(pn, 0)
        # 야간: SP3M3는 기본품번(10자리) 키로 조회
        if lc == 'SP3M3' and has_night:
            base_pn = pn[:10]  # 컬러코드 제거
            if base_pn not in _sp3m3_ngt_used:
                g_ngt_raw = gp_n.get(base_pn, 0)
                if g_ngt_raw > 0:
                    _sp3m3_ngt_used.add(base_pn)
            else:
                g_ngt_raw = 0  # 같은 기본품번의 후속 컬러 → 이미 할당됨
        else:
            g_ngt_raw = gp_n.get(pn, 0)
        g_day_qty = g_day_raw * usage
        g_ngt_qty = g_ngt_raw * usage if has_night else 0

        # 구ERP 수량 (Usage 환산)
        e_day_raw = ep_d.get(pn, 0)
        e_day_qty = e_day_raw * usage

        # 금액 계산 — 구ERP 방식 통일
        # 주간금액 = 순수주간수량 × 단가
        # 야간금액 = 야간수량 × 단가 × 1.3 (기본100% + 가산30%)
        # GERP '정상'행 = 총수량(주+야) → 순수주간 = 정상 - 추가
        # SD9A01: GERP 순수주간 = 정상 - 추가 (SP3M3는 야간=170원 고정, 분리 불필요)
        if lc == 'SD9A01':
            g_pure_day = g_day_qty - g_ngt_qty
        else:
            g_pure_day = g_day_qty
        g_day_amt = round(g_pure_day * price)
        g_ngt_amt = calc_night_price(lc, price, g_ngt_qty)
        e_day_amt = round(e_day_qty * price)

        # 구ERP 야간: SP3M3는 GERP 야간 동일 적용 (구ERP에 야간 데이터 없음)
        if lc == 'SP3M3' and has_night:
            e_ngt_qty = g_ngt_qty
            e_ngt_amt = g_ngt_amt
            e_tot_qty = e_day_qty + e_ngt_qty
        else:
            e_ngt_raw = ep_n.get(pn, 0) if has_night else 0
            e_ngt_qty = e_ngt_raw * usage if has_night else 0
            e_ngt_amt = calc_night_price(lc, price, e_ngt_qty)
            e_tot_raw = ep_t.get(pn, 0) if has_night else e_day_raw
            e_tot_qty = e_tot_raw * usage

        # 야간 총 정산금액 (GERP 기준): 주간+야간 합산
        gerp_total_amt = g_day_amt + g_ngt_amt

        # GERP 원본 금액 (다중단가 비교용)
        gerp_orig_day_amt = round(gp_d_amt.get(pn, 0))
        if lc == 'SP3M3' and has_night:
            # 야간수량과 동일하게 첫 품번에만 할당 (컬러별 중복 방지)
            base_pn = pn[:10]
            if g_ngt_raw > 0:  # 이 품번이 야간수량을 할당받은 경우만
                gerp_orig_ngt_amt = round(gp_n_amt.get(base_pn, 0))
            else:
                gerp_orig_ngt_amt = 0
        else:
            gerp_orig_ngt_amt = round(gp_n_amt.get(pn, 0))

        price_judgment = sd9_price_judgment(lc, price, g_ngt_qty)

        # 조립품번: 기준정보 우선, 없으면 GERP fallback
        assy_key = f"{lc}|{pn}|{price}"
        ref_assy = r.get('assy_part', '')
        gerp_assy = gerp_assy_lookup.get(assy_key, '')
        assy_part = ref_assy if ref_assy else gerp_assy

        # 지원분 (0109 외 업체) — SD9A01만 해당
        sup_info = []
        if lc == 'SD9A01' and pn in support_detail:
            sup_info = support_detail[pn]

        row = {
            'part_no':          pn,
            'assy_part':        assy_part,
            'price':            price,
            'usage':            usage,
            'price_type':       r['price_type'],
            'vtype':            r['vtype'],
            'gerp_day_qty':     g_pure_day,
            'gerp_day_amt':     g_day_amt,
            'gerp_ngt_qty':     g_ngt_qty,
            'gerp_ngt_amt':     g_ngt_amt,
            'gerp_total_amt':   gerp_total_amt,
            'gerp_orig_day_amt': gerp_orig_day_amt,
            'gerp_orig_ngt_amt': gerp_orig_ngt_amt,
            'erp_day_qty':      e_day_qty,
            'erp_day_amt':      e_day_amt,
            'erp_ngt_qty':      e_ngt_qty,
            'erp_ngt_amt':      e_ngt_amt,
            'erp_tot_qty':      e_tot_qty,   # 주간+야간 합산 총수량 (원본합산 검증용)
            'price_judgment':   price_judgment,
            'support':          sup_info,     # 지원분: [{vendor, line_code, day_qty, night_qty}]
        }
        detail.append(row)

        total_gerp_day_qty += g_pure_day
        total_gerp_day_amt += g_day_amt
        total_gerp_ngt_qty += g_ngt_qty
        total_gerp_ngt_amt += g_ngt_amt
        total_erp_day_qty  += e_day_qty
        total_erp_day_amt  += e_day_amt
        total_erp_ngt_qty  += e_ngt_qty
        total_erp_ngt_amt  += e_ngt_amt

    # SP3M3: 미매칭 RSP (모품번 못 찾음) → GERP 원본금액 그대로 적용
    if lc == 'SP3M3' and has_night:
        for rsp_pn, rsp_qty in gp_n.items():
            if rsp_pn.startswith('RSP') and rsp_qty > 0:
                ngt_amt = round(gp_n_amt.get(rsp_pn, 0))  # GERP 원본 야간금액
                row = {
                    'part_no':          rsp_pn,
                    'price':            round(ngt_amt / rsp_qty) if rsp_qty else 0,
                    'usage':            1,
                    'price_type':       'RSP미매칭',
                    'vtype':            '',
                    'gerp_day_qty':     0,
                    'gerp_day_amt':     0,
                    'gerp_ngt_qty':     rsp_qty,
                    'gerp_ngt_amt':     ngt_amt,
                    'gerp_total_amt':   ngt_amt,
                    'gerp_orig_day_amt': 0,
                    'gerp_orig_ngt_amt': ngt_amt,
                    'erp_day_qty':      0,
                    'erp_day_amt':      0,
                    'erp_ngt_qty':      0,
                    'erp_ngt_amt':      0,
                    'erp_tot_qty':      0,
                    'price_judgment':   None,
                }
                detail.append(row)
                # 합계 가산 안 함 — GERP 원본 night_amt_pivot에 이미 포함
                print(f"    RSP미매칭 {rsp_pn}: {rsp_qty}개, GERP원본 {ngt_amt:,}원 (합계 미가산)")

    # 미매핑 품번: 기준정보 단가 없음 → GERP 원본금액 fallback 적용
    unmatched_set = set(step4.get('unmatched_gerp', []))
    lc_day_items = gp_d  # day_pivot[lc]
    for pn in list(lc_day_items.keys()):
        if pn not in unmatched_set:
            continue
        um_day_qty = lc_day_items[pn]
        um_day_amt = round(gp_d_amt.get(pn, 0))
        um_ngt_qty = gp_n.get(pn, 0) if has_night else 0
        um_ngt_amt = round(gp_n_amt.get(pn, 0)) if has_night else 0
        um_price = round(um_day_amt / um_day_qty) if um_day_qty else 0
        um_total = um_day_amt + um_ngt_amt

        row = {
            'part_no':          pn,
            'assy_part':        gerp_assy_lookup.get(f"{lc}|{pn}|{um_price}", ''),
            'price':            um_price,
            'usage':            1,
            'price_type':       '미매핑_GERP단가',
            'vtype':            '',
            'gerp_day_qty':     um_day_qty,
            'gerp_day_amt':     um_day_amt,
            'gerp_ngt_qty':     um_ngt_qty,
            'gerp_ngt_amt':     um_ngt_amt,
            'gerp_total_amt':   um_total,
            'gerp_orig_day_amt': um_day_amt,
            'gerp_orig_ngt_amt': um_ngt_amt,
            'erp_day_qty':      0,
            'erp_day_amt':      0,
            'erp_ngt_qty':      0,
            'erp_ngt_amt':      0,
            'erp_tot_qty':      0,
            'price_judgment':   None,
        }
        detail.append(row)
        total_gerp_day_qty += um_day_qty
        total_gerp_day_amt += um_day_amt
        total_gerp_ngt_qty += um_ngt_qty
        total_gerp_ngt_amt += um_ngt_amt
        print(f"    미매핑 {pn}: {um_day_qty}개, GERP단가={um_price}, 금액={um_total:,}원")

    gerp_total = total_gerp_day_amt + total_gerp_ngt_amt
    erp_total  = total_erp_day_amt  + total_erp_ngt_amt
    diff       = gerp_total - erp_total

    lines_result[lc] = {
        'items':               detail,
        'total_gerp_day_qty':  total_gerp_day_qty,
        'total_gerp_day_amt':  total_gerp_day_amt,
        'total_gerp_ngt_qty':  total_gerp_ngt_qty,
        'total_gerp_ngt_amt':  total_gerp_ngt_amt,
        'total_gerp_amt':      gerp_total,
        'total_erp_day_qty':   total_erp_day_qty,
        'total_erp_day_amt':   total_erp_day_amt,
        'total_erp_ngt_qty':   total_erp_ngt_qty,
        'total_erp_ngt_amt':   total_erp_ngt_amt,
        'total_erp_amt':       erp_total,
        'diff_amt':            diff,
    }

    summary_rows.append({
        'line': lc,
        'name': LINE_INFO[lc]['name'],
        'gerp_amt': gerp_total,
        'erp_amt':  erp_total,
        'diff_amt': diff,
    })

    mark = '✓' if diff == 0 else '△'
    print(f"  {mark} {lc:10s}: GERP {gerp_total:>12,}  구ERP {erp_total:>12,}  차이 {diff:>+12,}")

# 전체 합계
grand_gerp = sum(r['gerp_amt'] for r in summary_rows)
grand_erp  = sum(r['erp_amt']  for r in summary_rows)
grand_diff = grand_gerp - grand_erp
print(f"\n  합계: GERP {grand_gerp:>12,}  구ERP {grand_erp:>12,}  차이 {grand_diff:>+12,}")

# ── JSON 저장 ─────────────────────────────────────────────────
result = {
    "step": 5,
    "timestamp": datetime.now().isoformat(),
    "month": MONTH,
    "lines": lines_result,
    "summary": summary_rows,
    "grand_gerp_amt": grand_gerp,
    "grand_erp_amt":  grand_erp,
    "grand_diff_amt": grand_diff,
    "unmatched_gerp": [],  # GERP 단가 fallback 적용 완료
}

with open(CACHE_STEP5, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"\n저장: {CACHE_STEP5}")
print("Step 5 완료")
