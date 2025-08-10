import os
from fpdf import FPDF

# 출력 폴더 보장
os.makedirs("data/reports", exist_ok=True)

pdf = FPDF(unit="mm", format="A4")
pdf.set_auto_page_break(True, margin=15)
pdf.set_left_margin(15); pdf.set_right_margin(15)
pdf.add_page()

# ✅ 유니코드 폰트 등록 (맑은 고딕)
FONT_PATH = r"C:\Windows\Fonts\malgun.ttf"
pdf.add_font("Malgun", "", FONT_PATH, uni=True)
pdf.set_font("Malgun", size=12)

pdf.multi_cell(0, 8, "안녕하세요! fpdf2 유니코드 폰트 테스트입니다.\n줄바꿈/한글도 정상 출력돼요.")
out = "data/reports/_fpdf_smoke_test.pdf"
pdf.output(out)
print("Wrote:", out)
