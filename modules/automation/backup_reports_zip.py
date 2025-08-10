
from modules.core.time_utils import now_utc, now_kst, iso_utc, monotonic
import os
import zipfile
from datetime import datetime

def backup_reports_zip():
    source_dir = "C:/giwanos/data/reports"
    backup_dir = "C:/giwanos/data/backups"
    date_str = now_kst().strftime("%Y%m%d")
    zip_path = os.path.join(backup_dir, f"weekly_report_{date_str}.zip")

    if not os.path.exists(source_dir):
        print(f"[백업 건너뜀] 보고서 폴더가 존재하지 않음: {source_dir}")
        return

    os.makedirs(backup_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arcname)
                print(f"[백업 포함] {arcname}")

    print(f"[✅ 보고서 압축 완료] → {zip_path}")



