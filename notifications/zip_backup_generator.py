import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import os
import zipfile
from datetime import datetime

base_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(base_dir, "loop_backups")
os.makedirs(output_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
zip_name = f"giwanos_backup_{timestamp}.zip"
zip_path = os.path.join(output_dir, zip_name)

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
    for folder, subdirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".py") or file.endswith(".md") or file.endswith(".json"):
                file_path = os.path.join(folder, file)
                arcname = os.path.relpath(file_path, base_dir)
                zipf.write(file_path, arcname)

print(f"✅ ZIP 백업 생성 완료: {zip_path}")
