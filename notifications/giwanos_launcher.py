import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import subprocess

print("🚀 GIWANOS 자동 실행 루프 시작\n")

base = "C:/giwanos/github_release_bundle"

scripts = [
    "file_sort_for_지완OS_v2.py",
    "loop_modules/report/generate_reflection_pdf.py",
    "loop_modules/sync/upload_final_runner.py",
    "zip_backup_generator.py"
]

for script in scripts:
    print(f"🚀 실행: {script}")
    subprocess.run(["python", script], cwd=base, check=True)

print("\n✅ 전체 루프 실행 완료!")
