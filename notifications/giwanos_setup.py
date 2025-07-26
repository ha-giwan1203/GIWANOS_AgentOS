import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import os
import shutil

folders = ["logs", "snapshots", "reports", "loop_agents"]
files_to_touch = [
    "loop_experience_log.json",
    "loop_dashboard_data.json"
]

def setup_giwanos():
    print("🔧 GIWANOS 설치 시작...")

    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"📁 폴더 생성됨: {folder}")

    for file in files_to_touch:
        if not os.path.exists(file):
            with open(file, "w", encoding="utf-8") as f:
                f.write("{}")
            print(f"📄 빈 파일 생성됨: {file}")

    if not os.path.exists(".env"):
        shutil.copy(".env.template", ".env")
        print("✅ .env 파일 생성 완료 (.env.template → .env 복사)")

    print("🎉 GIWANOS 설치 완료!")

if __name__ == "__main__":
    setup_giwanos()
