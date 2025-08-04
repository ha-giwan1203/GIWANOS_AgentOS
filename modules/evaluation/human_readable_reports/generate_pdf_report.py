import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def load_latest_analysis():
    try:
        with open("C:/giwanos/data/logs/api_cost_log.json", 'r', encoding='utf-8') as file:
            data = json.load(file)
            if data and "analysis_result" in data[-1]:
                return data[-1]["analysis_result"]
            return "No valid analysis result found"
    except Exception as e:
        return f"Error loading analysis result: {e}"

def generate_pdf_report(output_path: str = None):
    output_dir = "C:/giwanos/data/reports"
    os.makedirs(output_dir, exist_ok=True)
    if not output_path:
        date_str = datetime.now().strftime("%Y%m%d")
        output_path = f"{output_dir}/weekly_report_{date_str}.pdf"

    analysis_result = load_latest_analysis()

    c = canvas.Canvas(output_path, pagesize=letter)
    c.drawString(100, 750, "VELOS Weekly Report")
    c.drawString(100, 730, f"Generated on: {datetime.now().isoformat()}")
    c.drawString(100, 710, f"Analysis Result: {analysis_result}")
    c.showPage()
    c.save()

    print(f"[generate_pdf_report] PDF created: {output_path}")
    return output_path
