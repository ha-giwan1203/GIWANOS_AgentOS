#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 5 — 정산 계산
라인별 금액 계산 → JSON 저장 (Step7 엑셀 생성용 중간 데이터)

계산 규칙 (GERP 단가 기준 — 2026-04-05 변경):
  - 정산금액 = GERP 원본금액 직접 사용 (기준단가 재계산 아님)
  - 주간: GERP 원본 주간금액, 야간: GERP 원본 야간금액
  - SD9A01 단가기준판정: 단가 ≤ 500 → 야간가산, > 500 → 기본 (표시용)
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


def calc_night_price_erp(lc, price, night_qty):
    """구ERP 야간 정산금액 계산 (구ERP에는 GERP 원본 없으므로 기존 방식 유지)

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
    _processed_pns = set()  # 마스터 루프에서 처리된 품번 추적
    _gerp_amt_used = set()  # GERP 금액 이미 합계에 포함된 품번 (다중단가 중복 방지)

    for r in rows:
        pn    = r['part_no']
        price = r['price']
        usage = r['usage']
        _processed_pns.add(pn)
        is_first_gerp = pn not in _gerp_amt_used  # 다중단가: 첫 행만 GERP 합계에 포함

        # GERP 수량 (Usage 환산)
        g_day_raw = gp_d.get(pn, 0) if is_first_gerp else 0
        # 야간: SP3M3는 전체품번 우선 → 10자리 base fallback
        if lc == 'SP3M3' and has_night:
            ngt_key = pn if pn in gp_n else pn[:10]  # MO품번(12자리) 등 대응
            if ngt_key not in _sp3m3_ngt_used:
                g_ngt_raw = gp_n.get(ngt_key, 0)
                if g_ngt_raw > 0:
                    _sp3m3_ngt_used.add(ngt_key)
            else:
                g_ngt_raw = 0  # 같은 기본품번의 후속 컬러 → 이미 할당됨
        else:
            g_ngt_raw = gp_n.get(pn, 0) if is_first_gerp else 0
        g_day_qty = g_day_raw * usage
        g_ngt_qty = g_ngt_raw * usage if has_night else 0

        # 구ERP 수량 (Usage 환산) — 다중단가 각 행별 개별 계산
        e_day_raw = ep_d.get(pn, 0)
        e_day_qty = e_day_raw * usage

        # 금액 계산 — GERP 원본금액 기준 (2026-04-05 변경)
        # GERP 정산: GERP 원본금액 직접 사용 (기준단가 재계산 아님)
        # 다중단가: GERP 금액은 품번당 1회만 합계에 포함 (is_first_gerp)
        # 구ERP: 기존 방식 유지 (기준단가 × 수량, 각 행별 개별 계산)
        if lc == 'SD9A01':
            g_pure_day = g_day_qty - g_ngt_qty
        else:
            g_pure_day = g_day_qty
        # GERP: 원본금액 직접 사용 (첫 행만)
        g_day_amt = round(gp_d_amt.get(pn, 0)) if is_first_gerp else 0
        if lc == 'SP3M3' and has_night:
            ngt_amt_key = pn if pn in gp_n_amt else pn[:10]
            if g_ngt_raw > 0:
                g_ngt_amt = round(gp_n_amt.get(ngt_amt_key, 0))
            else:
                g_ngt_amt = 0
        else:
            g_ngt_amt = round(gp_n_amt.get(pn, 0)) if (has_night and is_first_gerp) else 0
        _gerp_amt_used.add(pn)
        # 구ERP: 기준단가 × 수량 (기준단가 = 기준정보 파일 단가)
        e_day_amt = round(e_day_qty * price)

        # 구ERP 야간: SP3M3는 GERP 야간 동일 적용 (구ERP에 야간 데이터 없음)
        if lc == 'SP3M3' and has_night:
            e_ngt_qty = g_ngt_qty
            e_ngt_amt = g_ngt_amt
            e_tot_qty = e_day_qty + e_ngt_qty
        else:
            e_ngt_raw = ep_n.get(pn, 0) if has_night else 0
            e_ngt_qty = e_ngt_raw * usage if has_night else 0
            e_ngt_amt = calc_night_price_erp(lc, price, e_ngt_qty)
            e_tot_raw = ep_t.get(pn, 0) if has_night else e_day_raw
            e_tot_qty = e_tot_raw * usage

        # 야간 총 정산금액 (GERP 기준): 주간+야간 합산
        gerp_total_amt = g_day_amt + g_ngt_amt

        # GERP 원본 금액 = 정산금액과 동일 (GERP 기준 전환)
        gerp_orig_day_amt = g_day_amt
        gerp_orig_ngt_amt = g_ngt_amt

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
            if rsp_pn.startswith('RSP') and rsp_qty > 0 and rsp_pn not in _processed_pns:
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
                    'erp_ngt_qty':      rsp_qty,
                    'erp_ngt_amt':      ngt_amt,
                    'erp_tot_qty':      rsp_qty,
                    'price_judgment':   None,
                }
                detail.append(row)
                _processed_pns.add(rsp_pn)  # fallback 이중계산 방지
                # GERP 원본금액 기준 전환 — RSP미매칭도 합계에 포함
                total_gerp_ngt_qty += rsp_qty
                total_gerp_ngt_amt += ngt_amt
                # 구ERP 야간도 GERP 동일 적용 (SP3M3 구ERP 야간 = GERP 야간)
                total_erp_ngt_qty += rsp_qty
                total_erp_ngt_amt += ngt_amt
                print(f"    RSP미매칭 {rsp_pn}: {rsp_qty}개, GERP원본 {ngt_amt:,}원 (합계 가산)")

    # 미매핑/미처리 품번: GERP pivot에 있지만 마스터 루프에서 처리 안 된 품번 → GERP 원본금액 fallback
    # step4 unmatched뿐 아니라, 기준정보 다른 라인에는 있어도 이 라인에 없는 품번도 포함
    lc_all_parts = set(gp_d.keys())
    if has_night:
        lc_all_parts |= set(gp_n.keys())
    unprocessed = lc_all_parts - _processed_pns
    for pn in sorted(unprocessed):
        um_day_qty = gp_d.get(pn, 0)
        um_day_amt = round(gp_d_amt.get(pn, 0))
        # SP3M3 야간: 마스터 루프에서 base_pn(10자리)으로 이미 사용된 야간금액은 제외 (이중 계산 방지)
        if lc == 'SP3M3' and has_night and pn[:10] in _sp3m3_ngt_used:
            um_ngt_qty = 0
            um_ngt_amt = 0
        else:
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
        print(f"    미매핑 {pn}: 주간={um_day_qty}개/{um_day_amt:,}원 야간={um_ngt_qty}개/{um_ngt_amt:,}원")

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

# ── 오류 리스트 (라인별 차이 품번 유형 분류) ─────────────────
error_list = []
for lc in LINE_ORDER:
    ld = lines_result.get(lc, {})
    for r in ld.get('items', []):
        g_amt = r['gerp_total_amt']
        e_amt = r['erp_day_amt'] + r['erp_ngt_amt']
        if g_amt == e_amt:
            continue
        g_qty = r['gerp_day_qty'] + r['gerp_ngt_qty']
        e_qty = r['erp_day_qty'] + r['erp_ngt_qty']
        # 유형 판정
        if e_amt == 0 and g_amt > 0:
            etype = '구실적누락'
        elif g_amt == 0 and e_amt > 0:
            etype = 'GERP누락'
        elif r['price'] == 0:
            etype = '기준누락'
        elif g_qty != e_qty and g_qty > 0 and e_qty > 0:
            # 단가도 다른지 확인
            gerp_up = round(g_amt / g_qty) if g_qty else 0
            erp_up = r['price']
            if gerp_up != erp_up:
                etype = '단가+수량'
            else:
                etype = '수량차이'
        elif g_qty != e_qty:
            etype = '수량차이'
        else:
            # 수량 동일, 금액 다름 → 단가 차이
            gerp_up = round(g_amt / g_qty) if g_qty else 0
            erp_up = r['price']
            if gerp_up != erp_up:
                etype = '단가차이'
            else:
                etype = '정산차이'
        error_list.append({
            'line': lc, 'part_no': r['part_no'], 'type': etype,
            'price_type': r['price_type'],
            'gerp_qty': g_qty, 'erp_qty': e_qty,
            'gerp_amt': g_amt, 'erp_amt': e_amt,
            'diff_amt': g_amt - e_amt,
        })

# 요약 출력
from collections import Counter
type_cnt = Counter(e['type'] for e in error_list)
type_amt = {}
for e in error_list:
    type_amt[e['type']] = type_amt.get(e['type'], 0) + e['diff_amt']
print(f"\n오류 리스트: {len(error_list)}건")
for t in ['구실적누락', 'GERP누락', '수량차이', '정산차이', '기준누락']:
    if t in type_cnt:
        print(f"  {t}: {type_cnt[t]}건, {type_amt[t]:+,}원")

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
    "error_list": error_list,
}

with open(CACHE_STEP5, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"\n저장: {CACHE_STEP5}")
print("Step 5 완료")
