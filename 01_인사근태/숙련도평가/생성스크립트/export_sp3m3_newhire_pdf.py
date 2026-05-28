# -*- coding: utf-8 -*-
"""
SP3M3 신규 입사자 교육자료 xlsx → PDF 변환
- 페이지 헤더: 시트명 (공정번호·공정명)
- 페이지 푸터: 회사명 + 페이지 번호
- 시트별 1페이지 fit
- PDF 책갈피 자동 (시트명 기반)
"""
from pathlib import Path
import win32com.client as win32

BASE = Path(__file__).resolve().parent.parent
OUTDIR = BASE / "SP3M3_신규입사자 교육자료"

XLSX = OUTDIR / "SP3M3_신규입사자 교육자료.xlsx"
PDF = OUTDIR / "SP3M3_신규입사자 교육자료.pdf"

# Excel 상수
xlTypePDF = 0
xlQualityStandard = 0


def main():
    if not XLSX.exists():
        print(f"❌ 원본 xlsx 없음: {XLSX}")
        print("   먼저 create_sp3m3_newhire_v5.py 를 실행하세요.")
        return

    print(f"[1/3] Excel 열기: {XLSX.name}")
    excel = win32.gencache.EnsureDispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    wb = excel.Workbooks.Open(str(XLSX.resolve()))

    print(f"[2/3] 시트 {wb.Sheets.Count}개 페이지 헤더·푸터 설정...")
    for i in range(1, wb.Sheets.Count + 1):
        sheet = wb.Sheets(i)
        sheet_name = sheet.Name

        # 헤더 — 가운데에 공정명 굵게 (네이비)
        # &"폰트,스타일" 형식 / &숫자 폰트 크기 / &K색상RGB 글자색
        sheet.PageSetup.CenterHeader = (
            f"&\"맑은 고딕,Bold\"&14&K1F4E79 SP3M3 공정 {sheet_name}"
        )
        sheet.PageSetup.LeftHeader = "&\"맑은 고딕\"&9&K6B7280 (유)삼송  ·  안전벨트 ASS'Y"
        sheet.PageSetup.RightHeader = "&\"맑은 고딕\"&9&K6B7280 신규 입사자 교육자료"

        # 푸터
        sheet.PageSetup.LeftFooter = "&\"맑은 고딕\"&9&K6B7280 사수 확인 ____________"
        sheet.PageSetup.CenterFooter = "&\"맑은 고딕\"&9&K6B7280 26.05  ·  Rev.1"
        sheet.PageSetup.RightFooter = "&\"맑은 고딕\"&9&K6B7280 &P / &N"

        # 헤더·푸터 여백
        sheet.PageSetup.HeaderMargin = 14
        sheet.PageSetup.FooterMargin = 14

        # 시트 1개를 A4 1페이지에 강제 fit (가로·세로 모두 1페이지)
        sheet.PageSetup.Zoom = False
        sheet.PageSetup.FitToPagesWide = 1
        sheet.PageSetup.FitToPagesTall = 1

    print(f"[3/3] PDF 내보내기 → {PDF.name}")
    if PDF.exists():
        PDF.unlink()

    wb.ExportAsFixedFormat(
        Type=xlTypePDF,
        Filename=str(PDF.resolve()),
        Quality=xlQualityStandard,
        IncludeDocProperties=True,
        IgnorePrintAreas=False,
        OpenAfterPublish=False,
    )

    wb.Close(SaveChanges=False)
    excel.Quit()

    size_kb = PDF.stat().st_size / 1024
    print(f"\n✅ 완료 — {PDF}")
    print(f"   크기: {size_kb:,.1f} KB")


if __name__ == "__main__":
    main()
