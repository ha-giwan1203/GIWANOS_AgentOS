# -*- coding: utf-8 -*-
"""
SP3M3 신규 입사자 교육자료 — 모던 디자인 PDF (HTML+CSS → Playwright)
xlsx의 데이터를 가져와 완전히 다른 시각 표현으로 PDF 생성.
- 표지 1페이지 (그라데이션, 큰 타이포)
- 공정별 1페이지 × 6 (히어로 헤더 + 카드 그리드 + 타임라인)
- 모던 컬러 팔레트 (네이비, 골드 액센트)
"""
from __future__ import annotations
import sys
from pathlib import Path

# v5 데이터 로더 재사용
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from create_sp3m3_newhire_v5 import (
    load_processes, load_eval_forms, load_workstd_steps, extract_parts,
    PROC_OVERRIDES,
)

OUTDIR = SCRIPT_DIR.parent / "SP3M3_신규입사자 교육자료"
PDF_OUT = OUTDIR / "SP3M3_신규입사자 교육자료_디자인.pdf"
HTML_OUT = OUTDIR / "_preview.html"


# ─────────────────────────────────────────────
# HTML/CSS 템플릿
# ─────────────────────────────────────────────
CSS = """
@page {
  size: A4 portrait;
  margin: 0;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body {
  font-family: 'Pretendard', 'Malgun Gothic', '맑은 고딕', sans-serif;
  color: #1a1a1a;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
.page {
  width: 210mm;
  height: 296mm;  /* 297mm은 PDF에서 1mm 넘침 → 다음 페이지 흘러감 방지 */
  break-after: page;
  page-break-after: always;
  position: relative;
  overflow: hidden;
}
.page:last-child { break-after: auto; page-break-after: auto; }

/* ─────────── 표지 ─────────── */
.cover {
  background: linear-gradient(135deg, #0b1d3a 0%, #1e3a8a 60%, #1e40af 100%);
  color: #fff;
  padding: 18mm 18mm 14mm;
  display: flex;
  flex-direction: column;
  gap: 8mm;
}
.cover::before {
  content: '';
  position: absolute;
  top: -80mm; right: -80mm;
  width: 200mm; height: 200mm;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(250,204,21,0.2) 0%, transparent 60%);
}
.cover::after {
  content: '';
  position: absolute;
  bottom: -60mm; left: -40mm;
  width: 160mm; height: 160mm;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(59,130,246,0.25) 0%, transparent 60%);
}
.cover-top { position: relative; z-index: 2; }
.cover-brand {
  font-size: 11pt; letter-spacing: 0.3em; opacity: 0.7;
  text-transform: uppercase; margin-bottom: 4mm;
}
.cover-line {
  display: inline-block;
  background: rgba(250, 204, 21, 0.15);
  border: 1px solid rgba(250, 204, 21, 0.4);
  color: #facc15;
  padding: 2mm 5mm;
  border-radius: 50px;
  font-size: 10pt;
  font-weight: 600;
  letter-spacing: 0.1em;
}
.cover-main { position: relative; z-index: 2; }
.cover-title {
  font-size: 40pt;
  font-weight: 900;
  line-height: 1.05;
  margin-bottom: 4mm;
  letter-spacing: -0.02em;
}
.cover-title .accent { color: #facc15; }
.cover-subtitle {
  font-size: 14pt;
  font-weight: 300;
  opacity: 0.85;
  line-height: 1.5;
  max-width: 140mm;
}
.cover-bottom {
  margin-top: auto;
  position: relative; z-index: 2;
  display: flex; justify-content: space-between; align-items: flex-end;
  border-top: 1px solid rgba(255,255,255,0.2);
  padding-top: 6mm;
}
.cover-bottom .item .label {
  font-size: 8pt; opacity: 0.6; text-transform: uppercase;
  letter-spacing: 0.2em; margin-bottom: 1mm;
}
.cover-bottom .item .value {
  font-size: 13pt; font-weight: 600;
}
.cover-toc {
  margin-top: 4mm;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 3mm;
  position: relative; z-index: 2;
}
.cover-spacer { flex: 1; }
.toc-item {
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 3mm;
  padding: 4mm;
  backdrop-filter: blur(10px);
}
.toc-item .no {
  font-size: 22pt; font-weight: 900;
  color: #facc15; line-height: 1;
  margin-bottom: 2mm;
}
.toc-item .name {
  font-size: 9pt; opacity: 0.85; line-height: 1.3;
}

/* ─────────── 공정 페이지 ─────────── */
.proc {
  background: #f8fafc;
  padding: 0;
  display: flex;
  flex-direction: column;
}
.hero {
  background: linear-gradient(135deg, #0b1d3a 0%, #1e3a8a 100%);
  color: #fff;
  padding: 10mm 16mm 12mm;
  position: relative;
  overflow: hidden;
}
.hero::after {
  content: '';
  position: absolute;
  top: 0; right: 0;
  width: 80mm; height: 100%;
  background: linear-gradient(45deg, transparent 30%, rgba(250,204,21,0.08) 100%);
}
.hero-top {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 8.5pt; letter-spacing: 0.2em; opacity: 0.7;
  text-transform: uppercase; margin-bottom: 4mm;
  position: relative; z-index: 2;
}
.hero-no {
  font-size: 9pt;
  background: rgba(250,204,21,0.15);
  border: 1px solid rgba(250,204,21,0.5);
  color: #facc15;
  padding: 1.5mm 4mm;
  border-radius: 50px;
  font-weight: 700;
}
.hero-title {
  font-size: 24pt;
  font-weight: 800;
  line-height: 1.15;
  letter-spacing: -0.01em;
  position: relative; z-index: 2;
  max-width: 165mm;
}
.hero-meta {
  display: flex; gap: 6mm; margin-top: 5mm;
  font-size: 9.5pt;
  position: relative; z-index: 2;
}
.hero-meta .chip {
  background: rgba(255,255,255,0.1);
  border-radius: 50px;
  padding: 1.5mm 5mm;
}
.hero-meta .chip strong { color: #facc15; margin-right: 2mm; }

/* 본문 그리드 */
.body {
  flex: 1;
  padding: 8mm 16mm 6mm;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto auto 1fr;
  gap: 4mm;
}

/* 카드 공통 */
.card {
  background: #fff;
  border-radius: 3mm;
  padding: 4mm 5mm;
  box-shadow: 0 0.5mm 2mm rgba(15,23,42,0.06);
  border: 1px solid #e5e7eb;
}
.card h3 {
  font-size: 10pt;
  font-weight: 700;
  color: #0b1d3a;
  display: flex; align-items: center; gap: 2mm;
  margin-bottom: 3mm;
  padding-bottom: 2mm;
  border-bottom: 1px solid #e5e7eb;
}
.card h3 .badge {
  background: #facc15;
  color: #0b1d3a;
  width: 5mm; height: 5mm;
  border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 8pt; font-weight: 900;
}

/* 사용 부품 칩 */
.parts {
  grid-column: 1 / 3;
}
.parts-list {
  display: flex; flex-wrap: wrap; gap: 2mm;
}
.part-chip {
  background: #eff6ff;
  color: #1e3a8a;
  border: 1px solid #bfdbfe;
  padding: 1.5mm 4mm;
  border-radius: 50px;
  font-size: 10pt;
  font-weight: 600;
}

/* 작업 순서 타임라인 */
.steps { grid-column: 1 / 2; }
.timeline {
  display: flex; flex-direction: column; gap: 2mm;
  position: relative;
}
.step {
  display: flex; gap: 3mm; align-items: flex-start;
  font-size: 8.5pt; line-height: 1.4;
}
.step-no {
  background: #0b1d3a; color: #fff;
  min-width: 5.5mm; height: 5.5mm;
  border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 7.5pt; font-weight: 700;
  flex-shrink: 0;
}
.step-no.identifier {
  background: #facc15; color: #0b1d3a;
}
.step-text { color: #334155; flex: 1; padding-top: 0.5mm; }

/* OK / NG 표 */
.okng { grid-column: 2 / 3; }
.okng-table {
  display: flex; flex-direction: column; gap: 1.5mm;
}
.okng-row {
  display: grid;
  grid-template-columns: 5mm 1fr 1fr;
  gap: 2mm;
  font-size: 7.5pt;
  line-height: 1.3;
}
.okng-row .no {
  color: #94a3b8; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.okng-row .ok {
  background: linear-gradient(135deg, #ecfdf5, #d1fae5);
  color: #065f46;
  padding: 1.5mm 2.5mm;
  border-radius: 1.5mm;
  border-left: 1.2mm solid #10b981;
  font-weight: 600;
}
.okng-row .ng {
  background: linear-gradient(135deg, #fef2f2, #fee2e2);
  color: #991b1b;
  padding: 1.5mm 2.5mm;
  border-radius: 1.5mm;
  border-left: 1.2mm solid #ef4444;
  font-weight: 600;
}

/* 안전 박스 */
.safety { grid-column: 1 / 3; }
.safety-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 2mm;
}
.safety-item {
  background: linear-gradient(135deg, #fffbeb, #fef3c7);
  border: 1px solid #fde68a;
  border-radius: 2mm;
  padding: 2.5mm;
  text-align: center;
  font-size: 7.5pt;
  line-height: 1.3;
  color: #78350f;
}
.safety-item .icon {
  font-size: 13pt;
  margin-bottom: 1mm;
}

/* 푸터 */
.proc-footer {
  background: #0b1d3a;
  color: rgba(255,255,255,0.7);
  padding: 4mm 16mm;
  font-size: 8pt;
  display: flex; justify-content: space-between; align-items: center;
}
.proc-footer .signs span {
  margin-right: 6mm;
}
.proc-footer .signs i {
  display: inline-block;
  width: 25mm;
  border-bottom: 1px dotted rgba(255,255,255,0.4);
  margin-left: 2mm;
}
.proc-footer .page-no {
  color: #facc15;
  font-weight: 700;
}
"""


PAGE_COVER = """
<div class="page cover">
  <div class="cover-top">
    <div class="cover-brand">(유)삼송  ·  Seat Belt Assembly</div>
    <div class="cover-line">▸ SP3M3 LINE</div>
  </div>

  <div class="cover-main">
    <h1 class="cover-title">신규 입사자<br><span class="accent">교육자료</span></h1>
    <p class="cover-subtitle">
      자동차 안전벨트 조립 라인.<br>
      1개의 이종·누락이 차량 1대 리콜로 이어지는 라인입니다.<br>
      빠르게보다 정확하게 — 의심되면 즉시 사수 확인.
    </p>
  </div>

  <div class="cover-toc">
__TOC__
  </div>

  <div class="cover-bottom">
    <div class="item">
      <div class="label">Issued</div>
      <div class="value">2026.05</div>
    </div>
    <div class="item">
      <div class="label">Revision</div>
      <div class="value">Rev.1</div>
    </div>
    <div class="item">
      <div class="label">Owner</div>
      <div class="value">생산관리</div>
    </div>
  </div>
</div>
"""


def _toc_html(procs):
    items = []
    for p in procs:
        items.append(f"""
      <div class="toc-item">
        <div class="no">{p['no']}</div>
        <div class="name">{p['name']}</div>
      </div>""")
    return "".join(items)


SAFETY_ITEMS = [
    ("⚙️", "일상 점검<br>에어압 0.4~0.6 MPa"),
    ("🔄", "초물표<br>차종 변경 시 첫 5개 사수"),
    ("🧤", "장갑·귀마개<br>회전부·압입부 손가락 금지"),
    ("🛑", "이상 시 즉시 중지<br>관리자 보고"),
    ("⚠️", "의심 시 라인 멈춤<br>NG 흘려보내지 말 것"),
]


def _build_proc_page(proc, eval_data, ws_data, parts, page_no, total_pages):
    ov = PROC_OVERRIDES.get(proc["no"], {})
    parts_label = ov.get("parts_label", "사용 부품")
    skip_id = ov.get("skip_identifier_check", False)

    # 부품 칩
    parts_chips = "".join(f'<span class="part-chip">{p}</span>' for p in parts)

    # 작업 순서 타임라인
    steps = ws_data.get("steps", [])
    step_html = []
    for i, s in enumerate(steps, 1):
        is_id = (not skip_id) and i == 1 and "식별표" in s
        cls = "step-no identifier" if is_id else "step-no"
        step_html.append(f'<div class="step"><span class="{cls}">{i}</span><span class="step-text">{s}</span></div>')

    # OK/NG 표
    okng_html = []
    if eval_data:
        items = eval_data["items"][:6]
        crits = eval_data["criteria"][:6]
        for i, (it, (q, _u, y)) in enumerate(zip(items, crits), 1):
            okng_html.append(f"""
            <div class="okng-row">
              <div class="no">{i}</div>
              <div class="ok">✓ {q or ''}</div>
              <div class="ng">✗ {y or ''}</div>
            </div>""")

    # 안전 박스
    safety_html = "".join(
        f'<div class="safety-item"><div class="icon">{icon}</div>{text}</div>'
        for icon, text in SAFETY_ITEMS
    )

    return f"""
<div class="page proc">
  <div class="hero">
    <div class="hero-top">
      <span>SP3M3 LINE</span>
      <span class="hero-no">PROCESS · {proc['no']}</span>
    </div>
    <h2 class="hero-title">{proc['name']}</h2>
    <div class="hero-meta">
      <span class="chip"><strong>요구레벨</strong>{proc['level']}</span>
      <span class="chip"><strong>참조</strong>작업표준서 시트 {ov.get('ref_sheet', '자동 매칭')}</span>
      <span class="chip"><strong>목표</strong>입사 1개월 내 단독 작업</span>
    </div>
  </div>

  <div class="body">
    <div class="card parts">
      <h3><span class="badge">①</span> {parts_label}</h3>
      <div class="parts-list">{parts_chips}</div>
    </div>

    <div class="card steps">
      <h3><span class="badge">②</span> 작업 순서</h3>
      <div class="timeline">{''.join(step_html)}</div>
    </div>

    <div class="card okng">
      <h3><span class="badge">③</span> 합격 vs 불합격</h3>
      <div class="okng-table">{''.join(okng_html)}</div>
    </div>

    <div class="card safety">
      <h3><span class="badge">④</span> 꼭 지킬 것 — 안전·이종·일상점검</h3>
      <div class="safety-grid">{safety_html}</div>
    </div>
  </div>

  <div class="proc-footer">
    <div class="signs">
      <span>사수 사인<i></i></span>
      <span>라인장 확인<i></i></span>
      <span>날짜<i></i></span>
    </div>
    <div class="page-no">{page_no} / {total_pages}</div>
  </div>
</div>
"""


def build_html():
    procs = load_processes()
    ef = load_eval_forms()

    cover = PAGE_COVER.replace("__TOC__", _toc_html(procs))
    total = len(procs) + 1  # 표지 포함
    pages = [cover]
    for i, p in enumerate(procs, start=2):
        ws_data = load_workstd_steps(p["no"])
        parts = extract_parts(p, ef.get(p["no"]), ws_data)
        pages.append(_build_proc_page(p, ef.get(p["no"]), ws_data, parts, i, total))

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>SP3M3 신규 입사자 교육자료</title>
  <style>{CSS}</style>
</head>
<body>
{''.join(pages)}
</body>
</html>
"""
    return html


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    print("[1/3] HTML 생성...")
    html = build_html()
    HTML_OUT.write_text(html, encoding="utf-8")
    print(f"  → {HTML_OUT.name}")

    print("[2/3] Playwright PDF 변환...")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(HTML_OUT.resolve().as_uri())
        page.wait_for_load_state("networkidle")
        page.emulate_media(media="screen")  # print 미디어가 absolute/flex 일부를 잘라먹음 — screen 강제
        if PDF_OUT.exists():
            PDF_OUT.unlink()
        page.pdf(
            path=str(PDF_OUT.resolve()),
            print_background=True,
            prefer_css_page_size=True,  # CSS @page 우선 — format/margin 인자와 충돌 방지
        )
        browser.close()

    print(f"[3/3] 완료 — {PDF_OUT}")
    print(f"   크기: {PDF_OUT.stat().st_size / 1024:,.1f} KB")


if __name__ == "__main__":
    main()
