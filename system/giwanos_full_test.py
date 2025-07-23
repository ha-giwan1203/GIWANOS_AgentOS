import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)


import os
from dotenv import load_dotenv

# .env 로딩
load_dotenv()

print("\n🚀 GIWANOS 마스터 루프 (전체 테스트) 시작\n")

# 루트 기준
ROOT = "C:/giwanos"

# 1. 회고 PDF 생성
print("▶ 회고 PDF 생성")
os.system(f"python {ROOT}/generate_reflection_pdf.py")

# 2. 회고 md 전송
print("\n▶ 회고 .md 전송")
os.system(f"python {ROOT}/send_reflection_md.py")

# 3. PDF 전송 (Notion)
print("\n▶ 회고 PDF Notion 전송")
os.system(f"python {ROOT}/upload_final_runner.py")

# 4. GitHub 전송 루프 (실전)
print("\n▶ GitHub 전송 루프")
os.system(f"python {ROOT}/GIWANOS_upload.py")

# 5. ZIP 백업 생성
print("\n▶ ZIP 백업 생성")
os.system(f"python {ROOT}/zip_backup_generator.py")

# 6. 사고 판단 기록
print("\n▶ 사고 판단 루프")
os.system(f"python {ROOT}/repeat_judge_runner.py")

print("\n✅ GIWANOS 전체 테스트 완료\n")
