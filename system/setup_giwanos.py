import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import os
import subprocess

print("🔧 GIWANOS 설치 자동화 시작")

if not os.path.exists(".env"):
    print("⚠️ .env 파일이 없습니다. 수동 설정이 필요합니다.")
else:
    print("✅ .env 파일 확인됨")

print("📦 의존성 설치 시작...")
subprocess.run(["pip", "install", "-r", "requirements.txt"])
print("✅ GIWANOS 설치 완료")
