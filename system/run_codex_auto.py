
import subprocess

print("🔁 Codex 자동 실행 시작...")

try:
    subprocess.run(["python", "advanced_modules/check_and_fix_all.py"], check=True)
    subprocess.run(["python", "advanced_modules/docstring_writer.py"], check=True)
    subprocess.run(["python", "advanced_modules/generate_code_docs.py"], check=True)
    print("✅ Codex 자동 분석 완료")
except subprocess.CalledProcessError:
    print("❌ 자동 실행 중 오류 발생")
