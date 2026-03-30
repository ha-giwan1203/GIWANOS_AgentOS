#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 7 — HTML 대시보드 생성 + PNG 변환
# v1: 현재월 단독 대시보드용. 전월 비교 기능 제외.

입력:  _cache/step7_visualization_input.json  (step7_시각화입력생성.py 출력)
출력:  _cache/월간_조립비_대시보드.html
       _cache/월간_조립비_대시보드.png   (Playwright)

실행:
    python step7_대시보드.py            # HTML + PNG
    python step7_대시보드.py --html-only # HTML만 (Playwright 없어도 가능)
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from _pipeline_config import CACHE_DIR

VIS_INPUT  = os.path.join(CACHE_DIR, 'step7_visualization_input.json')
HTML_OUT   = os.path.join(CACHE_DIR, '월간_조립비_대시보드.html')
PNG_OUT    = os.path.join(CACHE_DIR, '월간_조립비_대시보드.png')
TMPL_DIR   = os.path.join(os.path.dirname(__file__), 'templates')
TMPL_FILE  = 'step7_dashboard.html.j2'

print("=" * 60)
print("Step 7: HTML 대시보드 생성")
print("=" * 60)

# ── 입력 로드 ─────────────────────────────────────────────────
if not os.path.exists(VIS_INPUT):
    print(f"[ERROR] visualization_input 없음: {VIS_INPUT}")
    print("  먼저 step7_시각화입력생성.py 를 실행하세요.")
    sys.exit(1)

with open(VIS_INPUT, encoding='utf-8') as f:
    vis = json.load(f)

meta       = vis['report_meta']
summary    = vis['summary']
line_costs = vis['line_costs']
anomalies  = vis['anomalies']
insights   = vis['insights']

# ── 차트용 데이터 준비 (금액 내림차순 정렬 유지) ──────────────
chart_data = {
    'labels'     : [r['line_name'] for r in line_costs],
    'gerp_values': [r['current_cost'] for r in line_costs],
    'erp_values' : [r['erp_cost'] for r in line_costs],
}

# ── Jinja2 렌더링 ─────────────────────────────────────────────
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    print("[ERROR] jinja2 미설치: pip install jinja2")
    sys.exit(1)

env = Environment(
    loader=FileSystemLoader(TMPL_DIR),
    autoescape=select_autoescape(['html']),
)
tmpl = env.get_template(TMPL_FILE)

html_content = tmpl.render(
    meta       = meta,
    summary    = summary,
    line_costs = line_costs,
    anomalies  = anomalies,
    insights   = insights,
    chart_data = chart_data,
)

with open(HTML_OUT, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"[완료] HTML: {HTML_OUT}")

# ── Playwright PNG 변환 ───────────────────────────────────────
def generate_png(html_path: str, png_path: str) -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[SKIP] playwright 미설치: pip install playwright && python -m playwright install chromium")
        return False

    abs_html = Path(html_path).resolve()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(f"file:///{abs_html.as_posix()}")
            # Chart.js 렌더 완료 대기
            page.wait_for_timeout(1200)
            page.screenshot(path=png_path, full_page=True)
            browser.close()
        print(f"[완료] PNG:  {png_path}")
        return True
    except Exception as e:
        print(f"[ERROR] PNG 생성 실패: {e}")
        return False

# ── 실행 분기 ─────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument('--html-only', action='store_true', help='HTML만 생성 (PNG 건너뜀)')
args = parser.parse_args()

if not args.html_only:
    generate_png(HTML_OUT, PNG_OUT)

print("=" * 60)
print(f"  기준월: {meta['base_month']}")
print(f"  총 조립비: {summary['total_cost']:,}원")
print(f"  라인: {summary['line_count']}개  |  이상치: {summary['anomaly_count']}건")
print(f"  검증: {summary['validation_result']}")
print("=" * 60)
