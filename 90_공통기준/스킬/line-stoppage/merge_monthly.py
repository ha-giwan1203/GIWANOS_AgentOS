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
from openpyxl.styles import Font, PatternFill, Alignment

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


HF = Font(bold=True, color="FFFFFF")
HB = PatternFill("solid", fgColor="305496")
HEAD = Alignment(horizontal="center", vertical="center")
TITLE = Font(bold=True, size=14, color="305496")
NOTE = Font(italic=True, color="C00000")


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

    # 통합집계
    ws = wb.create_sheet("통합집계", 0)
    ws.append([f"■ {yyyymm} 라인정지·라인교체 통합 — 대원테크(0109)"])
    ws["A1"].font = TITLE
    ws.append([])
    ws.append(["시스템", "청구유형", "건수", "금액(원)", "비고"])
    for c in ws[3]:
        c.font = HF; c.fill = HB; c.alignment = HEAD

    gerp_cnt, gerp_amt = parse_gerp_summary(xlsx)
    ws.append(["G-ERP 라인보상상세현황", "라인정지", gerp_cnt, gerp_amt, "본사 등록"])

    for label in ("라인정지", "재작업", "선별작업", "기타생산비용"):
        rs = qis.get(label, {}).get("rows", [])
        cnt = len(rs)
        amt = sum(to_int(r.get("TOTAL_REQUIRE") or r.get("REWARD_LINE") or 0) for r in rs)
        type_name = "라인교체" if label == "기타생산비용" else label
        note = "협력사 작성" if cnt > 0 else "협력사 작성 0"
        ws.append([f"QIS Claim ({label} 탭)", type_name, cnt, amt, note])

    ws.append([])
    ws.append(["※ 청구유형이 다르므로 단순 합산 금지. 정산 본체에 별도 라인으로 들어감."])
    ws.cell(ws.max_row, 1).font = NOTE

    # QIS 라인교체 귀책 세분
    if rows:
        ws.append([])
        ws.append(["■ QIS 라인교체 귀책 세분"])
        ws.cell(ws.max_row, 1).font = Font(bold=True, size=12, color="305496")
        ws.append(["귀책 부서", "건수", "금액(원)"])
        for c in ws[ws.max_row]:
            c.font = HF; c.fill = HB; c.alignment = HEAD
        by_dept = defaultdict(lambda: {"cnt": 0, "amt": 0})
        for r in rows:
            d = r.get("NAME_CHARGE") or r.get("DEPT_ING") or "?"
            by_dept[d]["cnt"] += 1
            by_dept[d]["amt"] += to_int(r.get("TOTAL_REQUIRE") or 0)
        for d, v in sorted(by_dept.items(), key=lambda x: -x[1]["amt"]):
            ws.append([d, v["cnt"], v["amt"]])

    for col, w in zip("ABCDE", (25, 18, 8, 14, 18)):
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
