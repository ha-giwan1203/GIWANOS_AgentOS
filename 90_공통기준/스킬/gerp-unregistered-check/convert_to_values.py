"""
정산_수식버전_MM월_VALUES.xlsx 의 모든 수식을 값으로 변환.
pywin32 Excel COM (DispatchEx — 별도 인스턴스, 본체 잠금 영향 X) → CalculateFull → 모든 시트 UsedRange.Value=Value → SaveAs.

사용법: python convert_to_values.py {VALUES.xlsx 경로}
"""
import argparse
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

import win32com.client as win32

ap = argparse.ArgumentParser()
ap.add_argument("path", help="VALUES.xlsx 경로 (절대 경로 권장)")
args = ap.parse_args()

SRC = Path(args.path).resolve()
if not SRC.exists():
    print(f"[ERROR] 파일 없음: {SRC}")
    sys.exit(1)

print(f"[1/5] Excel COM 인스턴스 기동...")
xl = win32.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
xl.AskToUpdateLinks = False
xl.ScreenUpdating = False

try:
    print(f"[2/5] 파일 열기: {SRC.name}")
    wb = xl.Workbooks.Open(str(SRC), UpdateLinks=0, ReadOnly=False)
    print(f"      시트 수: {wb.Worksheets.Count}")

    print(f"[3/5] CalculateFull 호출 (모든 수식 재계산)...")
    t0 = time.time()
    xl.CalculateFull()
    print(f"      소요: {time.time()-t0:.1f}초")

    print(f"[4/5] 모든 시트 수식 → 값 변환...")
    for ws in wb.Worksheets:
        try:
            ur = ws.UsedRange
            rows = ur.Rows.Count
            cols = ur.Columns.Count
            if rows > 0 and cols > 0:
                ur.Value = ur.Value
                print(f"      {ws.Name}: {rows}×{cols} 변환 완료")
        except Exception as e:
            print(f"      {ws.Name}: SKIP ({e})")

    print(f"[5/5] 저장...")
    wb.Save()
    wb.Close(SaveChanges=False)
    print(f"[DONE] {SRC}")

finally:
    xl.Quit()
    del xl
