from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path

def test_korean_pdf_reportlab():
    try:
        # Create PDF
        output_file = "C:/giwanos/data/reports/test_korean_reportlab_full.pdf"
        c = canvas.Canvas(output_file, pagesize=A4)
        
        # Set up coordinates (A4 size)
        width, height = A4
        
        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 100, "Korean PDF Test Report")
        
        # Korean text (may show as boxes without proper font)
        c.setFont("Helvetica", 12)
        y_position = height - 150
        
        c.drawString(100, y_position, "Korean Test - 한글 테스트")
        y_position -= 20
        
        c.drawString(100, y_position, "English text works fine")
        y_position -= 20
        
        c.drawString(100, y_position, "한글 보고서 정상 출력 확인")
        y_position -= 20
        
        c.drawString(100, y_position, "줄바꿈도 OK")
        y_position -= 20
        
        # Try to add Korean font if available
        try:
            # Try Windows Korean fonts
            korean_fonts = [
                "C:/Windows/Fonts/malgun.ttf",
                "C:/Windows/Fonts/gulim.ttc",
                "C:/Windows/Fonts/batang.ttc"
            ]
            
            font_added = False
            for font_path in korean_fonts:
                if Path(font_path).exists():
                    try:
                        pdfmetrics.registerFont(TTFont('Korean', font_path))
                        c.setFont("Korean", 12)
                        c.drawString(100, y_position - 20, "한글 폰트로 렌더링된 텍스트")
                        font_added = True
                        print(f"Successfully loaded Korean font: {font_path}")
                        break
                    except Exception as e:
                        print(f"Failed to load font {font_path}: {e}")
                        continue
            
            if not font_added:
                c.setFont("Helvetica", 12)
                c.drawString(100, y_position - 20, "Korean font not available - using default")
                
        except Exception as e:
            print(f"Font loading error: {e}")
            c.setFont("Helvetica", 12)
            c.drawString(100, y_position - 20, "Font loading failed - using default")
        
        # Add some more content
        y_position -= 60
        c.drawString(100, y_position, "PDF Generation Test Results:")
        y_position -= 20
        c.drawString(100, y_position, "- Basic PDF creation: OK")
        y_position -= 20
        c.drawString(100, y_position, "- English text rendering: OK")
        y_position -= 20
        c.drawString(100, y_position, "- Korean text rendering: Needs proper font")
        
        # Save the PDF
        c.save()
        print(f"PDF OK -> {output_file}")
        
    except Exception as e:
        print(f"Error creating PDF: {e}")

if __name__ == "__main__":
    test_korean_pdf_reportlab()


