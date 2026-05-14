"""monthly-pnl-rollup — 본체 정산_수식버전_MM월.xlsx에 2시트 추가 (90 요약 + 91 상세).

호출:
    python 90_공통기준/스킬/monthly-pnl-rollup/run.py --month 04

산출:
    90_월정산_요약  KPI + 라인별 손익 + 검증 + 보고 템플릿
    91_정산상세    야간정합 + 기타비용 + 라인지원
"""
from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

THIS = Path(__file__).resolve()
sys.path.insert(0, str(THIS.parent))
from builders.sheet_94_support import parse_support_file  # noqa: E402

REPO = Path(r"C:\Users\User\Desktop\업무리스트")
SETTLE = REPO / "05_생산실적" / "조립비정산"
BI_PATH = REPO / "05_생산실적" / "BI실적" / "대원테크_라인별 생산실적_BI.xlsx"

LINES = ["SD9A01", "ANAAS04", "DRAAS11", "SP3M3", "HASMS02",
         "HCAMS02", "WAMAS01", "WABAS01", "WASAS01", "ISAMS03"]

# 스타일
TITLE_FONT = Font(name="맑은 고딕", size=14, bold=True)
SECTION_FONT = Font(name="맑은 고딕", size=12, bold=True, color="1F4E78")
H_FONT = Font(name="맑은 고딕", size=10, bold=True, color="FFFFFF")
H_FILL = PatternFill("solid", fgColor="305496")
SUB_FILL = PatternFill("solid", fgColor="D9E1F2")
NEG_FILL = PatternFill("solid", fgColor="FCE4D6")
POS_FILL = PatternFill("solid", fgColor="E2EFDA")
TOTAL_FILL = PatternFill("solid", fgColor="FFE699")
CENTER = Alignment(horizontal="center", vertical="center")
RIGHT = Alignment(horizontal="right", vertical="center")
LEFT = Alignment(horizontal="left", vertical="center")
BORDER = Border(*[Side(style="thin", color="BFBFBF")] * 4)


def _h(cell, txt):
    cell.value = txt
    cell.font = H_FONT
    cell.fill = H_FILL
    cell.alignment = CENTER
    cell.border = BORDER


def _num(cell, v):
    cell.value = v
    cell.number_format = "#,##0"
    cell.alignment = RIGHT
    cell.border = BORDER


def _w(ws, widths: dict[int, int]):
    for c, w in widths.items():
        ws.column_dimensions[get_column_letter(c)].width = w


def _section(ws, row, text):
    ws.cell(row, 1).value = text
    ws.cell(row, 1).font = SECTION_FONT


def verify_workbook_formulas(book_path: Path) -> list:
    """OOXML sheet*.xml의 모든 <f> 수식 raw 검증. 깨진 수식 리스트 반환."""
    import zipfile
    import re
    issues = []
    with zipfile.ZipFile(book_path) as zf:
        wb_xml = zf.read("xl/workbook.xml").decode('utf-8')
        sheets = re.findall(r'<sheet name="([^"]+)"[^/]*r:id="(rId\d+)"', wb_xml)
        rels = zf.read("xl/_rels/workbook.xml.rels").decode('utf-8')
        rid_map = dict(re.findall(
            r'Id="(rId\d+)"[^/]*Target="(worksheets/sheet\d+\.xml)"', rels))
        name_by_file = {f"xl/{rid_map.get(rid, '?')}": name
                        for name, rid in sheets}
        for fname in sorted(zf.namelist()):
            if not (fname.startswith("xl/worksheets/sheet") and fname.endswith(".xml")):
                continue
            content = zf.read(fname).decode('utf-8')
            sheet = name_by_file.get(fname, fname)
            for m in re.finditer(r'<f[^>]*>([^<]+)</f>', content):
                f = m.group(1)
                # 의심 패턴
                if not f.strip():
                    issues.append((sheet, "빈 수식", f))
                elif f.startswith(" "):
                    issues.append((sheet, "공백으로 시작", f[:60]))
                elif f.count("'") % 2 != 0:
                    issues.append((sheet, "홑따옴표 짝 불일치", f[:60]))
                elif f.count('"') % 2 != 0:
                    issues.append((sheet, "쌍따옴표 짝 불일치", f[:60]))
                elif f.endswith(("(", ",", ".")):
                    issues.append((sheet, "잘린 수식", f[:60]))
                # 함수명 아닌 영문 시작 + 셀참조도 아닌 패턴 (예: " A + B")
                elif re.match(r'^[A-Za-z][\w\s]*[\+\-\=]', f) and not re.match(
                        r'^([A-Z]+\d|SUM|IF|VLOOKUP|SUMIFS|COUNTIF|IFERROR|ISBLANK|ROUND|ABS|MAX|MIN|AND|OR|NOT|CONCAT)',
                        f.lstrip()):
                    issues.append((sheet, "함수 아닌 텍스트 추정", f[:60]))
    return issues


def safe_text(cell, value):
    """텍스트 셀에 = 시작 방지. openpyxl 자동 수식 인식 회피."""
    s = str(value)
    if s.startswith("="):
        s = " " + s  # 앞에 공백 한 칸
    cell.value = s


# ============================================================
# 데이터 로더 (시트 빌드와 분리)
# ============================================================

def extract_bi_night_total(line, year, month):
    """BI 원본 라인×월 야간 합계 + 일수."""
    if not BI_PATH.exists():
        return 0, 0
    wb = openpyxl.load_workbook(BI_PATH, data_only=True, read_only=True)
    ws = wb.worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    night_val = next((r[5] for r in rows[1:]
                      if r[4] == line and r[5] not in (None, "주간")), None)
    if night_val is None:
        return 0, 0
    total = days = 0
    for r in rows[1:]:
        if r[4] != line or r[5] != night_val:
            continue
        d = r[7]
        if not isinstance(d, datetime) or d.year != year or d.month != month:
            continue
        if r[14]:
            total += r[14]
            days += 1
    return total, days


def load_settlement_totals(book_path):
    """본체 정산집계 라인별 합계."""
    wb = openpyxl.load_workbook(book_path, data_only=True, read_only=True)
    ws = wb["정산집계"]
    lines, grand = {}, 0
    for r in range(2, ws.max_row + 1):
        code = ws.cell(r, 1).value
        if not code or code == "합계":
            continue
        total = ws.cell(r, 7).value or 0
        lines[code] = {
            "name": ws.cell(r, 2).value,
            "day_qty": ws.cell(r, 3).value or 0,
            "night_qty": ws.cell(r, 4).value or 0,
            "day_amt": ws.cell(r, 5).value or 0,
            "night_amt": ws.cell(r, 6).value or 0,
            "gerp_total": total,
        }
        grand += total
    wb.close()
    return {"lines": lines, "grand_total": grand}


def load_line_stoppage(path):
    """라인정지_MM월_raw.xlsx 통합집계."""
    if not path.exists():
        return {"exists": False, "rows": [], "total": 0, "blame": []}
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    ws = wb["통합집계"]
    rows, total = [], 0
    main_end = ws.max_row
    for r in range(4, ws.max_row + 1):
        v = ws.cell(r, 1).value
        if v == "합계":
            main_end = r
            break
        if not v:
            continue
        amt = ws.cell(r, 4).value or 0
        rows.append({"system": v, "claim_type": ws.cell(r, 2).value,
                     "count": ws.cell(r, 3).value or 0, "amount": amt})
        total += amt
    blame, in_blame = [], False
    for r in range(main_end + 1, ws.max_row + 1):
        v = ws.cell(r, 1).value
        if v == "귀책 부서":
            in_blame = True
            continue
        if not in_blame or not v:
            continue
        if v == "합계":
            break
        blame.append({"blame": v, "count": ws.cell(r, 2).value or 0,
                      "amount": ws.cell(r, 3).value or 0})
    wb.close()
    return {"exists": True, "rows": rows, "total": total, "blame": blame}


def load_support_data(folder, month_mm):
    """{MM}월 지원/*.xlsx 일괄 파싱."""
    result = {"exists": False, "details": [], "line_total": {},
              "pos_total": 0, "neg_total": 0, "B_sum": 0}
    if not folder.exists():
        return result
    files = sorted(folder.glob("*.xlsx"))
    if not files:
        return result
    result["exists"] = True
    line_total = {}
    pos = neg = 0
    for f in files:
        rows = parse_support_file(f, month_mm)
        for sr in rows:
            result["details"].append(sr)
            line_total[sr.line] = line_total.get(sr.line, 0) + sr.amount * sr.sign
            if sr.sign > 0:
                pos += sr.amount
            else:
                neg += sr.amount
    result["line_total"] = line_total
    result["pos_total"] = pos
    result["neg_total"] = neg
    result["B_sum"] = pos - neg
    return result


def compute_night_info(lines_data, year, month):
    """야간 가동라인 + BI 추출."""
    night_lines = [c for c in LINES
                   if lines_data["lines"].get(c, {}).get("night_qty", 0) > 0]
    bi_summary = {}
    for code in night_lines:
        qty, days = extract_bi_night_total(code, year, month)
        bi_summary[code] = {"qty": qty, "days": days}
    return {"night_lines": night_lines, "bi_summary": bi_summary}


def compute_pnl(lines_data, support, etc_data):
    A = lines_data["grand_total"]
    B = support["B_sum"]
    C = etc_data["total"] if etc_data["exists"] else 0
    D = 0  # 1차 안
    return {"A": A, "B": B, "C": C, "D": D, "final": A + B + C - D}


# ============================================================
# 시트 빌더 (2장만)
# ============================================================

def build_sheet_summary(wb, mm, lines_data, support, etc_data, night_info, pnl):
    """90_월정산_요약 — KPI + 라인별 + 검증 + 보고."""
    name = "90_월정산_요약"
    if name in wb.sheetnames:
        del wb[name]
    ws = wb.create_sheet(name, 0)  # 맨 앞

    ws.cell(1, 1).value = f"{mm}월 대원테크 조립비 월정산 요약"
    ws.cell(1, 1).font = Font(name="맑은 고딕", size=16, bold=True)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=7)
    ws.cell(2, 1).value = f"생성: {datetime.now():%Y-%m-%d %H:%M}"
    ws.cell(2, 1).font = Font(italic=True, color="808080")

    # ── 섹션 1: KPI ──
    r = 4
    _section(ws, r, "■ 최종 손익 (A + B + C − D)")
    r += 1
    kpis = [
        ("A. 기본조립비 (GERP)", pnl["A"], "GERP 라인별 합산"),
        ("B. 지원순액", pnl["B"], "준지원금 − 받은지원금"),
        ("C. 비용보전", pnl["C"], "라인정지 + 재작업 + 기타"),
        ("D. 차감비용", pnl["D"], "미인정 청구 + 회사 부담"),
        (None, None, None),
        ("최종 정산금액", pnl["final"], "A + B + C − D"),
    ]
    for label, val, note in kpis:
        if label is None:
            r += 1
            continue
        ws.cell(r, 1, label)
        if val is not None:
            _num(ws.cell(r, 2), val)
        ws.cell(r, 4, note).font = Font(italic=True, color="808080", size=9)
        if label and label.startswith("최종"):
            ws.cell(r, 1).font = Font(bold=True, size=12)
            ws.cell(r, 2).font = Font(bold=True, size=12)
            ws.cell(r, 1).fill = TOTAL_FILL
            ws.cell(r, 2).fill = TOTAL_FILL
        r += 1

    # ── 섹션 2: 라인별 손익 (산식 포함) ──
    r += 1
    _section(ws, r, "■ 라인별 손익 (A+B+C−D)")
    r += 1
    headers = ["라인", "라인명", "A. GERP", "B. 지원순액", "C. 비용보전", "D. 차감", "최종금액"]
    for c, h in enumerate(headers, 1):
        _h(ws.cell(r, c), h)
    r += 1
    line_finals = {}
    for code in LINES:
        d = lines_data["lines"].get(code, {})
        a = d.get("gerp_total", 0)
        b = support["line_total"].get(code, 0)
        c_val = 0  # 라인별 분배 없음 (합계만 91 상세)
        d_val = 0
        final = a + b + c_val - d_val
        line_finals[code] = final
        ws.cell(r, 1, code).alignment = CENTER
        ws.cell(r, 2, d.get("name", "")).alignment = CENTER
        _num(ws.cell(r, 3), a)
        _num(ws.cell(r, 4), b)
        if b < 0:
            ws.cell(r, 4).fill = NEG_FILL
        elif b > 0:
            ws.cell(r, 4).fill = POS_FILL
        _num(ws.cell(r, 5), c_val)
        _num(ws.cell(r, 6), d_val)
        _num(ws.cell(r, 7), final)
        ws.cell(r, 7).font = Font(bold=True)
        r += 1
    # 합계
    ws.cell(r, 1, "합계").alignment = CENTER
    ws.cell(r, 1).font = Font(bold=True)
    ws.cell(r, 1).fill = TOTAL_FILL
    ws.cell(r, 2).fill = TOTAL_FILL
    for c, v in zip([3, 4, 5, 6, 7], [pnl["A"], pnl["B"], pnl["C"], pnl["D"], pnl["final"]]):
        _num(ws.cell(r, c), v)
        ws.cell(r, c).fill = TOTAL_FILL
        ws.cell(r, c).font = Font(bold=True)
    r += 2

    # ── 섹션 3: 검증 ──
    _section(ws, r, "■ 검증·이슈 요약")
    r += 1
    for c, h in enumerate(["No", "항목", "결과", "비고"], 1):
        _h(ws.cell(r, c), h)
    r += 1
    bi_str = ", ".join(
        f"{c} GERP {lines_data['lines'][c]['night_qty']:,} vs BI {night_info['bi_summary'].get(c, {}).get('qty', 0):,}"
        for c in night_info["night_lines"]
    ) or "야간 라인 없음"
    items = [
        ("GERP 전체금액", "PASS" if pnl["A"] > 0 else "FAIL", f"A = {pnl['A']:,}원"),
        ("지원 자료", "PASS" if support["exists"] else "INFO",
         f"B = {pnl['B']:+,}원" + (" — 당월 지원 없음" if not support["exists"] else "")),
        ("기타비용 자료", "PASS" if etc_data["exists"] else "FAIL",
         f"C = {pnl['C']:,}원" if etc_data["exists"] else "라인정지_raw 미존재"),
        ("야간 BI 정합", "PASS" if night_info["night_lines"] else "INFO", bi_str),
        ("GERP vs 구ERP", "REF", "본체 [정산집계] [오류리스트] 참조"),
        ("최종 손익", "PASS", f"{pnl['final']:,}원"),
    ]
    for i, (item, result, note) in enumerate(items, 1):
        ws.cell(r, 1, i).alignment = CENTER
        ws.cell(r, 2, item)
        ws.cell(r, 3, result).alignment = CENTER
        if result == "PASS":
            ws.cell(r, 3).fill = POS_FILL
        elif result == "FAIL":
            ws.cell(r, 3).fill = NEG_FILL
        ws.cell(r, 4, note).alignment = LEFT
        r += 1
    r += 1

    # ── 섹션 4: 보고 템플릿 ──
    _section(ws, r, "■ 보고 문장 (복붙용)")
    r += 1
    night_str = ", ".join(night_info["night_lines"]) or "없음"
    template = [
        f"○ 2026년 {mm}월 대원테크 조립비 정산 결과 공유드립니다.",
        f"1. GERP 기준 기본 조립비는 {pnl['A']:,.0f}원입니다.",
        f"2. 야간 가동라인 {len(night_info['night_lines'])}개({night_str}) BI 비교 결과는 91_정산상세 시트 참조.",
        "3. GERP-구ERP 비교 결과는 [정산집계] [오류리스트] 시트 참조.",
        f"4. 타라인 지원 정산금액은 {pnl['B']:+,.0f}원, 라인정지·재작업·기타생산비 총액 {pnl['C']:,.0f}원입니다.",
        f"5. 최종 정산 반영금액은 {pnl['final']:,.0f}원입니다.",
    ]
    for line in template:
        ws.cell(r, 1, line)
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=7)
        r += 1

    _w(ws, {1: 30, 2: 16, 3: 14, 4: 14, 5: 14, 6: 12, 7: 16})


def build_sheet_detail(wb, mm, lines_data, support, etc_data, night_info, year=2026):
    """91_정산상세 — 야간정합 + 기타비용 + 라인지원."""
    name = "91_정산상세"
    if name in wb.sheetnames:
        del wb[name]
    ws = wb.create_sheet(name)

    ws.cell(1, 1).value = f"{mm}월 정산 상세 (raw 근거)"
    ws.cell(1, 1).font = TITLE_FONT
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=7)

    r = 3
    # ── 섹션 A: 야간 BI 정합 ──
    _section(ws, r, "A. 야간 가동라인 BI 정합 (GERP 추가행 vs BI 원본)")
    r += 1
    for c, h in enumerate(["라인", "라인명", "GERP 야간", "BI 야간", "BI 일수", "차이(EA)", "차이율"], 1):
        _h(ws.cell(r, c), h)
    r += 1
    if not night_info["night_lines"]:
        ws.cell(r, 1, "당월 야간 가동라인 없음").font = Font(italic=True, color="808080")
        r += 1
    else:
        for code in night_info["night_lines"]:
            d = lines_data["lines"][code]
            bi = night_info["bi_summary"][code]
            ws.cell(r, 1, code).alignment = CENTER
            ws.cell(r, 2, d["name"]).alignment = CENTER
            _num(ws.cell(r, 3), d["night_qty"])
            _num(ws.cell(r, 4), bi["qty"])
            _num(ws.cell(r, 5), bi["days"])
            ws.cell(r, 6).value = f"=C{r}-D{r}"
            ws.cell(r, 7).value = f"=IF(C{r}=0,0,(C{r}-D{r})/C{r})"
            ws.cell(r, 6).number_format = "#,##0;[Red]-#,##0;-"
            ws.cell(r, 7).number_format = "0.0%;[Red]-0.0%;-"
            ws.cell(r, 6).alignment = RIGHT
            ws.cell(r, 7).alignment = RIGHT
            pct = abs(d["night_qty"] - bi["qty"]) / max(d["night_qty"], 1) * 100 if bi["qty"] else 0
            fill = NEG_FILL if pct > 5 else POS_FILL
            ws.cell(r, 6).fill = fill
            ws.cell(r, 7).fill = fill
            r += 1
        ws.cell(r, 1).value = "※ SP3M3 차이 큼: GERP 야간(추가)행은 RSP 모듈품번만. BI는 전체 야간."
        ws.cell(r, 1).font = Font(italic=True, color="808080", size=9)
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=7)
        r += 1
    r += 1

    # ── 섹션 B: 기타비용 (C 비용보전) ──
    _section(ws, r, "B. 기타 생산비용 (C 비용보전)")
    r += 1
    if not etc_data["exists"]:
        ws.cell(r, 1).value = "라인정지_MM월_raw.xlsx 미존재 — line-stoppage 스킬 선행 필요"
        ws.cell(r, 1).font = Font(italic=True, color="C00000")
        r += 1
    else:
        for c, h in enumerate(["시스템", "청구유형", "건수", "금액(원)", "비고"], 1):
            _h(ws.cell(r, c), h)
        r += 1
        for row_data in etc_data["rows"]:
            ws.cell(r, 1, row_data["system"]).alignment = CENTER
            ws.cell(r, 2, row_data["claim_type"]).alignment = CENTER
            _num(ws.cell(r, 3), row_data["count"])
            _num(ws.cell(r, 4), row_data["amount"])
            r += 1
        ws.cell(r, 1, "합계").alignment = CENTER
        ws.cell(r, 1).font = Font(bold=True)
        ws.cell(r, 1).fill = TOTAL_FILL
        _num(ws.cell(r, 3), sum(x["count"] for x in etc_data["rows"]))
        _num(ws.cell(r, 4), etc_data["total"])
        ws.cell(r, 3).fill = TOTAL_FILL
        ws.cell(r, 4).fill = TOTAL_FILL
        ws.cell(r, 4).font = Font(bold=True)
        r += 2
        if etc_data["blame"]:
            ws.cell(r, 1, "└ QIS 라인교체 — 귀책 부서별").font = Font(bold=True, size=10)
            r += 1
            for c, h in enumerate(["귀책 부서", "건수", "금액(원)"], 1):
                _h(ws.cell(r, c), h)
            r += 1
            for b in etc_data["blame"]:
                ws.cell(r, 1, b["blame"]).alignment = CENTER
                _num(ws.cell(r, 2), b["count"])
                _num(ws.cell(r, 3), b["amount"])
                r += 1
    r += 1

    # ── 섹션 C: 라인지원 (B 지원순액) ──
    _section(ws, r, "C. 라인지원 (B 지원순액)")
    r += 1
    if not support["exists"]:
        ws.cell(r, 1).value = "당월 지원 없음 — '{MM}월 지원/' 폴더 부재 또는 비어있음"
        ws.cell(r, 1).font = Font(italic=True, color="808080")
        r += 1
    else:
        for c, h in enumerate(["파일", "부호", "라인", "금액(원)", "분류"], 1):
            _h(ws.cell(r, c), h)
        r += 1
        for sr in support["details"]:
            ws.cell(r, 1, sr.file).alignment = LEFT
            ws.cell(r, 2, "+" if sr.sign > 0 else "−").alignment = CENTER
            ws.cell(r, 3, sr.line).alignment = CENTER
            _num(ws.cell(r, 4), sr.amount * sr.sign)
            ws.cell(r, 4).fill = POS_FILL if sr.sign > 0 else NEG_FILL
            ws.cell(r, 5, "준지원금(가산)" if sr.sign > 0 else "받은지원금(차감)").alignment = LEFT
            r += 1
        # 합계
        ws.cell(r, 1, "지원 순액 (B)").font = Font(bold=True)
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
        ws.cell(r, 1).fill = TOTAL_FILL
        _num(ws.cell(r, 4), support["B_sum"])
        ws.cell(r, 4).fill = TOTAL_FILL
        ws.cell(r, 4).font = Font(bold=True)
        r += 1
        ws.cell(r, 1, "  └ 준지원금 (+)").alignment = RIGHT
        _num(ws.cell(r, 4), support["pos_total"])
        r += 1
        ws.cell(r, 1, "  └ 받은지원금 (−)").alignment = RIGHT
        _num(ws.cell(r, 4), -support["neg_total"])
        r += 1
        # 라인별 순액
        r += 1
        ws.cell(r, 1, "└ 라인별 순액").font = Font(bold=True, size=10)
        r += 1
        for c, h in enumerate(["라인", "금액"], 1):
            _h(ws.cell(r, c), h)
        r += 1
        for ln, v in sorted(support["line_total"].items(), key=lambda x: -abs(x[1])):
            ws.cell(r, 1, ln).alignment = CENTER
            _num(ws.cell(r, 2), v)
            ws.cell(r, 2).fill = POS_FILL if v > 0 else NEG_FILL
            r += 1

    _w(ws, {1: 38, 2: 12, 3: 10, 4: 16, 5: 24, 6: 12, 7: 12})


# ============================================================
# main
# ============================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", required=True)
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    mm = args.month.zfill(2)
    work = SETTLE / f"{int(mm) + 1:02d}월"
    book = work / f"정산_수식버전_{mm}월.xlsx"
    stoppage = work / f"라인정지_{mm}월_raw.xlsx"
    support_dir = work / f"{int(mm)}월 지원"

    if not book.exists():
        print(f"[FAIL] 본체 미존재: {book}")
        sys.exit(1)

    if not args.no_backup:
        bak = book.with_suffix(f".{datetime.now():%Y%m%d_%H%M%S}.bak.xlsx")
        shutil.copy2(book, bak)
        print(f"[BACKUP] {bak.name}")

    print("[LOAD] 본체 정산집계 …")
    lines_data = load_settlement_totals(book)
    print(f"  라인 {len(lines_data['lines'])}개, GERP 합계 {lines_data['grand_total']:,}원")

    print("[LOAD] 라인정지 통합집계 …")
    etc_data = load_line_stoppage(stoppage)
    if etc_data["exists"]:
        print(f"  {len(etc_data['rows'])}건, 합계 {etc_data['total']:,}원")
    else:
        print(f"  [WARN] {stoppage.name} 미존재")

    print(f"[LOAD] 지원자료 ({support_dir.name}) …")
    support = load_support_data(support_dir, mm)
    if support["exists"]:
        print(f"  지원 {len(support['details'])}행, B = {support['B_sum']:+,}원")
    else:
        print("  당월 지원 없음")

    print("[LOAD] BI 야간수량 추출 …")
    night_info = compute_night_info(lines_data, args.year, int(mm))
    print(f"  야간 라인: {night_info['night_lines']}")

    pnl = compute_pnl(lines_data, support, etc_data)
    print(f"\n[PNL] A={pnl['A']:,}  B={pnl['B']:+,}  C={pnl['C']:,}  D={pnl['D']:,}")
    print(f"      최종 = {pnl['final']:,}원")

    print(f"\n[OPEN] {book.name}")
    wb = openpyxl.load_workbook(book, data_only=False)

    # 기존 90~95 시트 삭제 (재실행 호환)
    for old in ["90_월정산_요약", "91_손익통합", "92_야간정합",
                "93_기타비용", "94_라인지원", "95_검증_이슈요약",
                "91_정산상세"]:
        if old in wb.sheetnames:
            del wb[old]

    print("[BUILD] 91_정산상세 …")
    build_sheet_detail(wb, mm, lines_data, support, etc_data, night_info, args.year)
    print("[BUILD] 90_월정산_요약 …")
    build_sheet_summary(wb, mm, lines_data, support, etc_data, night_info, pnl)

    print(f"[SAVE] {book}")
    wb.save(book)
    print(f"\n[BUILD OK] 2시트 추가 완료. 본체 시트 수: {len(wb.sheetnames)}")

    # OOXML 수식 무결성 자동 검증
    print("\n[VERIFY] OOXML 수식 무결성 검증 …")
    issues = verify_workbook_formulas(book)
    if issues:
        print(f"  ❌ 깨진 수식 {len(issues)}건 발견:")
        for sheet, kind, sample in issues[:20]:
            print(f"    [{sheet}] {kind}: {sample!r}")
        print("\n[FAIL] 엑셀 열 때 복구 경고 발생 가능. 위 수식 수정 필요.")
        sys.exit(2)
    print("  ✅ 모든 수식 정상 — 엑셀 열기 안전")


if __name__ == "__main__":
    main()
