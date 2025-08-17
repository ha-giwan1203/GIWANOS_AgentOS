from fpdf import FPDF
from pathlib import Path

FONT = Path("C:/giwanos/fonts/Nanum_Gothic/NanumGothic-Regular.ttf")
if not FONT.exists():
    raise SystemExit(f"폰트 파일 없음: {FONT}")

pdf = FPDF()
pdf.add_page()
pdf.add_font("Nanum","",str(FONT),uni=True)
pdf.set_font("Nanum", size=12)
pdf.multi_cell(0, 8, "한글 보고서 정상 출력 확인\n줄바꿈도 OK")
out = Path("C:/giwanos/data/reports/test_korean.pdf")
pdf.output(str(out))
print("PDF OK ->", out)
