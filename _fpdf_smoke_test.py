from fpdf import FPDF
pdf = FPDF(unit="mm", format="A4")
pdf.add_page()
pdf.set_font("Helvetica", size=12)
pdf.multi_cell(0, 8, "안녕하세요! fpdf2 테스트입니다.\n줄바꿈/한글 테스트.")
pdf.output("data/reports/_fpdf_smoke_test.pdf")
print("Wrote: data/reports/_fpdf_smoke_test.pdf")
