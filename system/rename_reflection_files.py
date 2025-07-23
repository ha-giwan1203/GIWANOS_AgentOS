import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import os
from datetime import datetime

REFLECTION_DIR = "C:/giwanos/reflections"

def get_timestamp_string(filepath):
    timestamp = os.path.getmtime(filepath)
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y%m%d_%H%M%S")

def rename_files():
    if not os.path.exists(REFLECTION_DIR):
        print("❌ reflections 폴더가 존재하지 않습니다.")
        return

    renamed = 0
    for filename in os.listdir(REFLECTION_DIR):
        full_path = os.path.join(REFLECTION_DIR, filename)
        if os.path.isfile(full_path) and not filename.startswith("loop_reflection_log_"):
            if filename.endswith(".pdf") or filename.endswith(".md"):
                ts = get_timestamp_string(full_path)
                ext = os.path.splitext(filename)[1]
                new_name = f"loop_reflection_log_{ts}{ext}"
                new_path = os.path.join(REFLECTION_DIR, new_name)
                os.rename(full_path, new_path)
                print(f"✅ {filename} → {new_name}")
                renamed += 1

    if renamed == 0:
        print("🔍 변경할 파일이 없습니다.")
    else:
        print(f"🎉 총 {renamed}개 파일 이름 변경 완료.")

if __name__ == "__main__":
    rename_files()