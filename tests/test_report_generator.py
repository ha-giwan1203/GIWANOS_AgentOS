# [ACTIVE] VELOS 테스트 보고서 생성기
# -*- coding: utf-8 -*-
# - 작은 용량의 간단한 보고서 생성
# - Email과 Slack 테스트용

import os
import json
import time
from pathlib import Path
from datetime import datetime

# 환경변수 로딩
try:
    from env_loader import load_env
    load_env()
except ImportError:
    pass

ROOT = Path(os.getenv("VELOS_ROOT") or r"C:\giwanos").resolve()
AUTO = ROOT / "data" / "reports" / "auto"
AUTO.mkdir(parents=True, exist_ok=True)

def create_test_report():
    """작은 용량의 테스트 보고서 생성"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 간단한 테스트 보고서 내용
    report_content = f"""# VELOS Test Report ({timestamp})

## System Status
- Status: OK
- Test: Email/Slack Dispatch
- Size: Small

## Summary
This is a test report for email and slack dispatch testing.
Generated at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Test Data
- Memory: 100 items
- Logs: 50 entries
- Status: Active

## End of Report
Test completed successfully.
"""
    
    # MD 파일 생성
    md_filename = f"velos_test_report_{timestamp}.md"
    md_path = AUTO / md_filename
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    # PDF 파일 생성 (간단한 텍스트 기반)
    pdf_filename = f"velos_test_report_{timestamp}.pdf"
    pdf_path = AUTO / pdf_filename
    
    # 간단한 PDF 생성 (텍스트만)
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        
        doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # 제목
        story.append(Paragraph(f"VELOS Test Report ({timestamp})", styles['Title']))
        story.append(Spacer(1, 12))
        
        # 내용
        story.append(Paragraph("System Status: OK", styles['Normal']))
        story.append(Paragraph("Test: Email/Slack Dispatch", styles['Normal']))
        story.append(Paragraph("Size: Small", styles['Normal']))
        story.append(Spacer(1, 12))
        
        story.append(Paragraph("This is a test report for email and slack dispatch testing.", styles['Normal']))
        story.append(Paragraph(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        
        doc.build(story)
        print(f"✅ 테스트 PDF 생성: {pdf_path}")
        
    except Exception as e:
        print(f"⚠️ PDF 생성 실패: {e}")
        # 대신 텍스트 파일 생성
        txt_filename = f"velos_test_report_{timestamp}.txt"
        txt_path = AUTO / txt_filename
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"✅ 테스트 TXT 생성: {txt_path}")
        return txt_path
    
    return pdf_path

if __name__ == "__main__":
    test_file = create_test_report()
    print(f"🎯 테스트 파일 생성 완료: {test_file}")
    print(f"📁 위치: {AUTO}")
