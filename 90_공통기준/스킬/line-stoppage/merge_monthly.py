"""월별 라인정지비용 통합 — G-ERP + QIS 단일 파일로.

선행 산출물:
  05_생산실적/조립비정산/{MM+1}월/라인정지_{MM}월_raw.xlsx  (run.py 출력)
  05_생산실적/조립비정산/{MM+1}월/라인정지_{MM}월_요약.md   (run.py 출력)
  05_생산실적/조립비정산/{MM+1}월/QIS청구_{MM}월_raw.json   (qis_extract.py 출력)

결과:
  - xlsx에 시트 추가: 통합집계 / QIS_기타생산비용 (등)
  - 요약 md를 G-ERP + QIS 통합 본문으로 재작성

사용:
  python merge_monthly.py --month 2026-04
"""
import sys, json, argparse, re, calendar
from pathlib import Path
from collections import defaultdict
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

REPO = Path(__file__).resolve().parents[3]


def to_int(v):
    try: return int(str(v).replace(",", "").replace(" ", "") or 0)
    except: return 0


def month_dirs(yyyymm: str):
    """도메인 관행: 매월 작업폴더 = 05_생산실적/조립비정산/{MM+1:02d}월/."""
    y, m = map(int, yyyymm.split("-"))
    nm = m + 1 if m < 12 else 1
    out = REPO / "05_생산실적" / "조립비정산" / f"{nm:02d}월"
    last = calendar.monthrange(y, m)[1]
    return out, f"{y:04d}-{m:02d}-01", f"{y:04d}-{m:02d}-{last:02d}", f"{m:02d}"


def parse_gerp_summary(xlsx_path: Path):
    """G-ERP 건수·합계 — xlsx 안 _meta 시트에서 읽음 (run.py가 저장)."""
    if not xlsx_path.exists(): return 0, 0
    try:
        wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
        if "_meta" in wb.sheetnames:
            ws = wb["_meta"]
            d = {}
            for r in range(2, ws.max_row + 1):
                k = ws.cell(r, 1).value; v = ws.cell(r, 2).value
                if k: d[k] = v
            wb.close()
            return int(d.get("count", 0) or 0), int(d.get("total_amount", 0) or 0)
        wb.close()
    except Exception as e:
        print(f"  [warn] _meta 시트 읽기 실패: {e}")
    return 0, 0


HF = Font(bold=True, color="FFFFFF", size=11, name="맑은 고딕")
HB = PatternFill("solid", fgColor="305496")
HEAD = Alignment(horizontal="center", vertical="center", wrap_text=True)
TITLE = Font(bold=True, size=16, color="305496", name="맑은 고딕")
NOTE = Font(italic=True, color="C00000", size=10, name="맑은 고딕")
BODY = Font(size=11, name="맑은 고딕")
THIN = Side(style="thin", color="9E9E9E")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
CENTER = Alignment(horizontal="center", vertical="center")
RIGHT = Alignment(horizontal="right", vertical="center")
LEFT = Alignment(horizontal="left", vertical="center", indent=1)
FMT_INT = "#,##0"
SUBTITLE = Font(bold=True, size=12, color="305496", name="맑은 고딕")
SUB_FILL = PatternFill("solid", fgColor="D9E1F2")


def merge(yyyymm: str):
    """xlsx 단일 파일에서 G-ERP _meta + QIS_* 시트 읽어서 통합집계 추가 + md 갱신."""
    out, df, dt, mm = month_dirs(yyyymm)
    xlsx = out / f"라인정지_{mm}월_raw.xlsx"
    md = out / f"라인정지_{mm}월_요약.md"

    if not xlsx.exists():
        raise FileNotFoundError(f"xlsx 없음: {xlsx} — run.py 먼저 실행")

    # QIS 4탭 데이터를 xlsx 시트에서 재구성
    wb_in = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    qis = {}
    for label in ("라인정지", "재작업", "선별작업", "기타생산비용"):
        sheet = f"QIS_{label}"
        rows = []
        if sheet in wb_in.sheetnames:
            ws = wb_in[sheet]
            headers = [c.value for c in ws[1]]
            for r in range(2, ws.max_row + 1):
                rows.append({h: ws.cell(r, i + 1).value for i, h in enumerate(headers)})
        qis[label] = {"rows": rows}
    wb_in.close()

    # 1. xlsx 시트 추가
    wb = openpyxl.load_workbook(xlsx)
    for name in ("통합집계", "QIS_기타생산비용"):
        if name in wb.sheetnames: del wb[name]

    # QIS 데이터 시트
    rows = qis.get("기타생산비용", {}).get("rows", [])
    if rows:
        ws = wb.create_sheet("QIS_기타생산비용")
        headers = list(rows[0].keys())
        ws.append(headers)
        for r in rows:
            ws.append([r.get(h, "") for h in headers])
        for c in ws[1]:
            c.font = HF; c.fill = HB; c.alignment = HEAD
        for i in range(1, len(headers) + 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = 18

    # 통합집계 시트 — 0건 제외, 디자인 보강
    ws = wb.create_sheet("통합집계", 0)
    ws.row_dimensions[1].height = 28
    ws["A1"] = f"{yyyymm}  라인정지·라인교체 통합  —  대원테크(0109)"
    ws["A1"].font = TITLE
    ws["A1"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.merge_cells("A1:E1")
    ws.append([])

    # 표 1: 시스템별 청구 (0건 제외)
    ws.append(["시스템", "청구유형", "건수", "금액(원)", "비고"])
    for c in ws[3]:
        c.font = HF; c.fill = HB; c.alignment = HEAD; c.border = BORDER
    ws.row_dimensions[3].height = 24

    gerp_cnt, gerp_amt = parse_gerp_summary(xlsx)
    body_rows = []
    if gerp_cnt > 0:
        body_rows.append(["G-ERP 라인보상상세현황", "라인정지", gerp_cnt, gerp_amt, "본사 직등록"])
    qis_summary = {}
    for label in ("라인정지", "재작업", "선별작업", "기타생산비용"):
        rs = qis.get(label, {}).get("rows", [])
        cnt = len(rs)
        amt = sum(to_int(r.get("TOTAL_REQUIRE") or r.get("REWARD_LINE") or 0) for r in rs)
        qis_summary[label] = (cnt, amt)
        if cnt == 0:
            continue  # 0건 제외
        type_name = "라인교체" if label == "기타생산비용" else label
        body_rows.append([f"QIS Claim · {label}", type_name, cnt, amt, "협력사 작성"])

    for row in body_rows:
        ws.append(row)
        r = ws.max_row
        ws.row_dimensions[r].height = 22
        ws.cell(r, 1).font = BODY; ws.cell(r, 1).alignment = LEFT; ws.cell(r, 1).border = BORDER
        ws.cell(r, 2).font = BODY; ws.cell(r, 2).alignment = CENTER; ws.cell(r, 2).border = BORDER
        ws.cell(r, 3).font = BODY; ws.cell(r, 3).alignment = RIGHT; ws.cell(r, 3).border = BORDER; ws.cell(r, 3).number_format = FMT_INT
        ws.cell(r, 4).font = BODY; ws.cell(r, 4).alignment = RIGHT; ws.cell(r, 4).border = BORDER; ws.cell(r, 4).number_format = FMT_INT
        ws.cell(r, 5).font = BODY; ws.cell(r, 5).alignment = LEFT; ws.cell(r, 5).border = BORDER

    # 0건 탭 메모 (작은 글씨로 한 줄)
    zero_tabs = [k for k, v in qis_summary.items() if v[0] == 0]
    if zero_tabs:
        ws.append([])
        ws.append([f"※ QIS 협력사 0건 탭(이번 달 작성 없음): {' / '.join(zero_tabs)}"])
        ws.cell(ws.max_row, 1).font = NOTE
        ws.merge_cells(start_row=ws.max_row, start_column=1, end_row=ws.max_row, end_column=5)

    ws.append([])
    ws.append(["※ 청구유형이 다르므로 단순 합산 금지. 정산 본체에 별도 라인으로 들어감."])
    ws.cell(ws.max_row, 1).font = NOTE
    ws.merge_cells(start_row=ws.max_row, start_column=1, end_row=ws.max_row, end_column=5)

    # 표 2: QIS 라인교체 귀책 세분 (0건 아닐 때만)
    if rows:
        ws.append([])
        ws.append([f"QIS 라인교체 {len(rows)}건 — 귀책 부서별"])
        ws.cell(ws.max_row, 1).font = SUBTITLE; ws.cell(ws.max_row, 1).fill = SUB_FILL
        ws.merge_cells(start_row=ws.max_row, start_column=1, end_row=ws.max_row, end_column=5)
        ws.row_dimensions[ws.max_row].height = 22

        ws.append(["귀책 부서", "건수", "금액(원)", "", ""])
        hr = ws.max_row
        ws.row_dimensions[hr].height = 22
        for col in (1, 2, 3):
            c = ws.cell(hr, col)
            c.font = HF; c.fill = HB; c.alignment = HEAD; c.border = BORDER

        by_dept = defaultdict(lambda: {"cnt": 0, "amt": 0})
        for r in rows:
            d = r.get("NAME_CHARGE") or r.get("DEPT_ING") or "?"
            by_dept[d]["cnt"] += 1
            by_dept[d]["amt"] += to_int(r.get("TOTAL_REQUIRE") or 0)
        for d, v in sorted(by_dept.items(), key=lambda x: -x[1]["amt"]):
            ws.append([d, v["cnt"], v["amt"], "", ""])
            r0 = ws.max_row
            ws.row_dimensions[r0].height = 22
            ws.cell(r0, 1).font = BODY; ws.cell(r0, 1).alignment = LEFT; ws.cell(r0, 1).border = BORDER
            ws.cell(r0, 2).font = BODY; ws.cell(r0, 2).alignment = RIGHT; ws.cell(r0, 2).border = BORDER; ws.cell(r0, 2).number_format = FMT_INT
            ws.cell(r0, 3).font = BODY; ws.cell(r0, 3).alignment = RIGHT; ws.cell(r0, 3).border = BORDER; ws.cell(r0, 3).number_format = FMT_INT
        # 합계 행
        ws.append(["합계", sum(v["cnt"] for v in by_dept.values()), sum(v["amt"] for v in by_dept.values()), "", ""])
        sr = ws.max_row
        ws.row_dimensions[sr].height = 24
        for col in (1, 2, 3):
            c = ws.cell(sr, col)
            c.font = Font(bold=True, size=11, name="맑은 고딕")
            c.fill = SUB_FILL
            c.border = BORDER
            c.alignment = RIGHT if col > 1 else CENTER
            if col > 1: c.number_format = FMT_INT

    # 컬럼 너비
    for col, w in zip("ABCDE", (30, 14, 10, 16, 22)):
        ws.column_dimensions[col].width = w

    wb.save(xlsx)
    print(f"[OK] xlsx 단일 파일: {xlsx.name}")
    print(f"     sheets: {wb.sheetnames}")
    # md는 별도로 안 만듦 — 통합집계 시트가 본문 역할


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--month", required=True, help="YYYY-MM")
    args = p.parse_args()
    merge(args.month)


if __name__ == "__main__":
    main()
