from fpdf import FPDF
import pathlib, sys

root_fonts = pathlib.Path("C:/giwanos/fonts")
print("🔍  fonts/ 안의 파일:", [f.name for f in root_fonts.iterdir()])

pdf = FPDF()
try:
    pdf.add_font("NotoSansCJK", "", str(root_fonts / "NotoSansCJKkr-Regular.otf"), uni=True)
    print("✅  NotoSansCJKkr-Regular.otf 로드 OK")
except Exception as e:
    print("❌  NotoSansCJK 폰트 로드 실패:", e)

try:
    pdf.add_font("NotoSansKR", "", str(root_fonts / "NotoSansKR-Regular.ttf"), uni=True)
    print("✅  NotoSansKR-Regular.ttf 로드 OK")
except Exception as e:
    print("❌  NotoSansKR 폰트 로드 실패:", e)
