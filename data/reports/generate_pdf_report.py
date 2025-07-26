from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import json
import os
from datetime import datetime

def create_pdf_from_insights(json_path: str) -> str:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    output_path = os.path.join("logs", "system_health.pdf")
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "GIWANOS 시스템 자동 분석 보고서")
    c.setFont("Helvetica", 11)
    c.drawString(50, height - 70, f"생성일: {datetime.today().strftime('%Y-%m-%d')}")

    y = height - 100
    for idx, item in enumerate(data, 1):
        if y < 100:
            c.showPage()
            y = height - 50
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, f"{idx}. [{item['category']}] ({item['severity']})")
        y -= 18
        c.setFont("Helvetica", 11)
        c.drawString(70, y, item['question'])
        y -= 18
        c.drawString(70, y, f"→ 결과: {item['issue']}")
        y -= 30

    c.showPage()
    c.save()
    return output_path
