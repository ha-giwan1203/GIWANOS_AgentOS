import json
import pathlib
from fpdf import FPDF

ROOT = pathlib.Path(__file__).resolve().parents[2]
DST = ROOT / "data/reports"
DST.mkdir(parents=True, exist_ok=True)

def load_latest_analysis():
    with open(ROOT / 'data/logs/api_cost_log.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data[-1]["analysis_result"]

def generate_pdf_report():
    analysis_result = load_latest_analysis()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "VELOS Weekly Report with GPT-4o Turbo Analysis", ln=True)
    pdf.ln(4)
    pdf.multi_cell(0, 10, f"GPT-4o Turbo Analysis:\n{analysis_result}")

    pdf_name = f"weekly_report_{datetime.now().strftime('%Y-%m-%d')}.pdf"
    pdf_path = DST / pdf_name
    pdf.output(str(pdf_path))

    return str(pdf_path)

if __name__ == "__main__":
    generate_pdf_report()
