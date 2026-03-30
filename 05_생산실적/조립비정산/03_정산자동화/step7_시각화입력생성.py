#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 7 — 시각화 입력 JSON 생성
# v1: 현재월 단독 대시보드용. 전월 비교 기능 제외.

목적:
    step5_settlement.json + step6_validation.json 을 읽어
    HTML 대시보드 생성용 step7_visualization_input.json 을 출력한다.

데이터 구조 (검증 완료 2026-03-30):
    s5['summary']       : list[{line, name, gerp_amt, erp_amt, diff_amt}]
    s5['grand_gerp_amt']: int  — 전체 GERP 합계
    s5['grand_diff_amt']: int  — 전체 차이
    s5['lines']         : dict[line_code -> {total_gerp_amt, diff_amt, ...}]  (보조용)
    s5['unmatched_gerp']: list — 미매핑 GERP 행
    s6['overall']       : str  — PASS / WARNING / CRITICAL_FAIL
    s6['checks']        : list[{no, name, status, severity, detail}]
    s6['warning']       : int
    s6['critical_fail'] : int

출력:
    _cache/step7_visualization_input.json

실행:
    python step7_시각화입력생성.py
"""

import os, sys, json
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from _pipeline_config import CACHE_DIR, CACHE_STEP5, MONTH, LINE_INFO

CACHE_STEP6  = os.path.join(CACHE_DIR, 'step6_validation.json')
OUTPUT_FILE  = os.path.join(CACHE_DIR, 'step7_visualization_input.json')

print("=" * 60)
print("Step 7: 시각화 입력 JSON 생성")
print("=" * 60)

# ── 입력 파일 로드 ────────────────────────────────────────────
if not os.path.exists(CACHE_STEP5):
    print(f"[ERROR] step5 결과 없음: {CACHE_STEP5}")
    sys.exit(1)

with open(CACHE_STEP5, encoding='utf-8') as f:
    s5 = json.load(f)

s6 = None
if os.path.exists(CACHE_STEP6):
    with open(CACHE_STEP6, encoding='utf-8') as f:
        s6 = json.load(f)
    print(f"[step6] overall={s6['overall']}  warning={s6['warning']}  critical_fail={s6['critical_fail']}")
else:
    print("[step6] 없음 — 이상치 섹션 생략")

# ── summary → line_costs 변환 ─────────────────────────────────
# 기준: s5['summary'] (라인별 GERP 금액 / 구ERP 금액 / 차이)
# 금액 내림차순 정렬, rank 부여

summary_rows = s5['summary']   # list[{line, name, gerp_amt, erp_amt, diff_amt}]
total_cost   = s5['grand_gerp_amt']

line_costs = []
for row in summary_rows:
    share = round((row['gerp_amt'] / total_cost * 100), 2) if total_cost else 0.0
    line_costs.append({
        'line_code'   : row['line'],
        'line_name'   : row['name'],
        'current_cost': row['gerp_amt'],
        'erp_cost'    : row['erp_amt'],
        'diff_amount' : row['diff_amt'],
        'share_rate'  : share,
    })

# 금액 내림차순 rank
line_costs.sort(key=lambda x: x['current_cost'], reverse=True)
for i, item in enumerate(line_costs, 1):
    item['rank'] = i

# ── top_changes (증감 상위/하위 5) ───────────────────────────
sorted_diff = sorted(line_costs, key=lambda x: x['diff_amount'], reverse=True)
top_changes = {
    'increase': [{'line_name': r['line_name'], 'diff_amount': r['diff_amount']}
                 for r in sorted_diff if r['diff_amount'] > 0][:5],
    'decrease': [{'line_name': r['line_name'], 'diff_amount': r['diff_amount']}
                 for r in sorted_diff if r['diff_amount'] < 0][-5:],
}

# ── 이상치 목록 (step6 checks 중 FAIL / WARNING) ─────────────
anomalies = []
if s6:
    for chk in s6['checks']:
        if chk['status'] in ('FAIL', 'WARNING', 'CRITICAL_FAIL'):
            anomalies.append({
                'no'      : chk['no'],
                'name'    : chk['name'],
                'status'  : chk['status'],
                'severity': chk['severity'],
                'detail'  : chk['detail'],
            })

anomaly_count = len(anomalies)

# ── 3줄 인사이트 자동 생성 ────────────────────────────────────
top_line    = line_costs[0] if line_costs else None
top_inc     = top_changes['increase'][0] if top_changes['increase'] else None
top_dec     = top_changes['decrease'][0] if top_changes['decrease'] else None
overall     = s6['overall'] if s6 else 'N/A'

insights = []
insights.append(
    f"당월 총 조립비는 {total_cost:,}원"
    + (f", 최대 라인은 {top_line['line_name']}({top_line['current_cost']:,}원, {top_line['share_rate']}%)" if top_line else "")
)
if top_inc:
    insights.append(f"주요 증가 라인: {top_inc['line_name']} (+{top_inc['diff_amount']:,}원)")
elif top_dec:
    insights.append(f"주요 감소 라인: {top_dec['line_name']} ({top_dec['diff_amount']:,}원)")
else:
    insights.append("라인별 증감 없음")

if anomaly_count == 0:
    insights.append(f"검증 결과 {overall} — 이상치 없음")
else:
    insights.append(f"검증 결과 {overall} — 확인 필요 {anomaly_count}건")

assert len(insights) == 3, "insights는 정확히 3줄이어야 함"

# ── 합계 검증 ─────────────────────────────────────────────────
line_sum = sum(r['current_cost'] for r in line_costs)
if round(line_sum) != round(total_cost):
    print(f"[ERROR] line_costs 합계({line_sum:,}) != grand_gerp_amt({total_cost:,})")
    sys.exit(1)

share_sum = sum(r['share_rate'] for r in line_costs)
if abs(share_sum - 100.0) > 0.5:
    print(f"[WARNING] share_rate 합계 = {share_sum:.2f}% (반올림 오차 확인)")

# ── 최종 JSON 조립 ────────────────────────────────────────────
vis_input = {
    'report_meta': {
        'report_type'     : 'monthly_settlement_dashboard',
        'base_month'      : f"2026-{MONTH}",
        'generated_at'    : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'source_pipeline' : 'settlement_step7',
        'source_version'  : 'v1.0.0',
        'company_name'    : '대원테크',
        'currency'        : 'KRW',
        'unit'            : '원',
    },
    'summary': {
        'total_cost'      : total_cost,
        'erp_total_cost'  : s5['grand_erp_amt'],
        'diff_total'      : s5['grand_diff_amt'],
        'line_count'      : len(line_costs),
        'anomaly_count'   : anomaly_count,
        'validation_result': overall,
    },
    'line_costs'  : line_costs,
    'top_changes' : top_changes,
    'anomalies'   : anomalies,
    'insights'    : insights,
    'chart_options': {
        'show_pie_chart'      : True,
        'show_treemap'        : False,
        'show_top_changes'    : True,
        'show_anomalies_table': True,
    },
}

# ── 저장 ──────────────────────────────────────────────────────
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(vis_input, f, ensure_ascii=False, indent=2)

print("=" * 60)
print("완료")
print(f"  출력: {OUTPUT_FILE}")
print(f"  기준월: {vis_input['report_meta']['base_month']}")
print(f"  총 조립비: {total_cost:,}원")
print(f"  라인 수: {len(line_costs)}개")
print(f"  이상치: {anomaly_count}건")
print(f"  검증: {overall}")
print("=" * 60)
for ins in insights:
    print(f"  · {ins}")
print("=" * 60)
