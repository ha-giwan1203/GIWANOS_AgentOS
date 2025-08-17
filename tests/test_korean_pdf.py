from fpdf import FPDF
from pathlib import Path

def test_korean_pdf():
    try:
        # Try different font paths
        font_paths = [
            "C:/giwanos/fonts/Nanum_Gothic/NanumGothic-Regular.ttf",
            "C:/giwanos/fonts/Nanum_Gothic/NotoSansKR-Regular.ttf",
            "C:/Windows/Fonts/malgun.ttf",  # Windows Korean font
            "C:/Windows/Fonts/gulim.ttc"    # Windows Korean font
        ]
        
        pdf = FPDF()
        pdf.add_page()
        
        # Try to add Korean font
        font_added = False
        for font_path in font_paths:
            try:
                if Path(font_path).exists():
                    print(f"Trying font: {font_path}")
                    pdf.add_font("Korean", "", font_path)
                    pdf.set_font("Korean", size=12)
                    font_added = True
                    break
            except Exception as e:
                print(f"Failed to load font {font_path}: {e}")
                continue
        
        if not font_added:
            # Fallback to default font
            print("Using default font")
            pdf.set_font("Arial", size=12)
        
        # Add content
        pdf.multi_cell(0, 8, "한글 보고서 정상 출력 확인\n줄바꿈도 OK")
        pdf.multi_cell(0, 8, "English text also works")
        
        # Output
        out = Path("C:/giwanos/data/reports/test_korean.pdf")
        pdf.output(str(out))
        print(f"PDF OK -> {out}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_korean_pdf()


