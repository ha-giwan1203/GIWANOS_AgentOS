# 🚀 VELOS 전체 파일 경로 추출기 (가상환경 제외 버전)
# 🔒 파일명 고정: export_giwanos_structure.py
# 📂 저장 위치: C:/giwanos/scripts/

import os

BASE_DIR = "C:/giwanos"
OUTPUT_FILE = os.path.join(BASE_DIR, "giwanos_file_structure.txt")
EXCLUDE_DIRS = {"venv", ".venv", "__pycache__", ".git", ".mypy_cache"}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for root, dirs, files in os.walk(BASE_DIR):
        # ❌ 제외 디렉토리 필터링
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            full_path = os.path.join(root, file)
            f.write(full_path + "\n")

print(f"✅ 전체 파일 경로를 '{OUTPUT_FILE}'에 저장했습니다. (가상환경 제외)")
