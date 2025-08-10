
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.report.generate_pdf_report import generate_pdf_report

if __name__ == "__main__":
    print("🧪 VELOS 보고서 생성 테스트 시작")
    output_path = generate_pdf_report()
    print(f"✅ 리포트 생성 완료: {output_path}")


