
import subprocess
from pathlib import Path

ROOT = Path(".")
target_files = list(ROOT.glob("*.py"))
fixer = "error_autofixer.py"

print("🛠️ 전체 Python 파일 오류 검사 및 수정 제안 시작")

for file in target_files:
    if file.name == fixer or file.name.startswith("fixed_"):
        continue
    print(f"🔍 검사 중: {file}")
    result = subprocess.run(["python", "error_autofixer.py", str(file)], capture_output=True, text=True)
    print(result.stdout)

print("✅ 전체 검사 및 자동 수정 완료")
