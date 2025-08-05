
"""
VELOS 시스템 정리 루프 (중간 상세 출력 버전)

- 삭제 수 + 삭제 파일 일부 이름 출력
- 압축 대상 수 + 포함된 대표 파일 출력
- 로그 저장 여부 및 경로 출력
"""

import os
import logging
import json
import zipfile
import warnings
from datetime import datetime, timedelta

# 외부 로그 억제
for noisy in ["fontTools", "fpdf"]:
    logging.getLogger(noisy).setLevel(logging.WARNING)

warnings.filterwarnings("ignore")

LOG_FILE = "C:/giwanos/data/logs/report_cleanup_log.json"

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def cleanup_old_files(directory, days_to_keep=30, extensions=None, log_records=None, label=None):
    cutoff = datetime.now() - timedelta(days=days_to_keep)
    deleted = []
    if not os.path.exists(directory):
        logging.info(f"📂 {label or directory}: 디렉토리 없음")
        return 0

    for root, _, files in os.walk(directory):
        for file in files:
            if extensions and not file.endswith(tuple(extensions)):
                continue
            path = os.path.join(root, file)
            try:
                modified = datetime.fromtimestamp(os.path.getmtime(path))
                if modified < cutoff:
                    os.remove(path)
                    deleted.append(file)
                    if log_records is not None:
                        log_records.append({
                            "file": file,
                            "path": path,
                            "deleted_at": datetime.now().isoformat(),
                            "age_days": (datetime.now() - modified).days,
                            "folder": directory
                        })
            except:
                continue

    if deleted:
        logging.info(f"🗑️ {label or directory}: {len(deleted)}개 삭제됨 → 예: {', '.join(deleted[:3])}...")
    else:
        logging.info(f"✅ {label or directory}: 삭제된 항목 없음")

    return len(deleted)

def cleanup_disk_usage(log_records):
    return sum([
        cleanup_old_files("C:/giwanos/data/logs", 3, [".log", ".jsonl", ".json"], log_records, label="logs/"),
        cleanup_old_files("C:/giwanos/data/snapshots", 3, [".zip", ".bak"], log_records, label="snapshots/")
    ])

def cleanup_reports(log_records):
    return sum([
        cleanup_old_files("C:/giwanos/data/reports", 30, [".pdf", ".md", ".html", ".txt"], log_records, label="reports/"),
        cleanup_old_files("C:/giwanos/data/reflections", 30, [".json", ".md", ".txt"], log_records, label="reflections/")
    ])

def save_cleanup_log(log_records):
    if not log_records:
        logging.info("📝 삭제 로그 없음 → 저장 생략")
        return None

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
                if not isinstance(existing, list):
                    existing = []
        else:
            existing = []
    except:
        existing = []

    existing.extend(log_records)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)

    logging.info(f"📝 삭제 로그 저장 완료: {LOG_FILE}")
    return LOG_FILE

def backup_reports_zip():
    source_dir = "C:/giwanos/data/reports"
    backup_dir = "C:/giwanos/data/backups"
    date_str = datetime.now().strftime("%Y%m%d")
    zip_path = os.path.join(backup_dir, f"weekly_report_{date_str}.zip")
    included = []

    if not os.path.exists(source_dir):
        return "[백업 생략] 보고서 폴더 없음"

    os.makedirs(backup_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arcname)
                included.append(file)

    if included:
        logging.info(f"[✅ 보고서 압축 완료] {len(included)}개 포함됨 → 예: {', '.join(included[:3])}...")
    else:
        logging.info("[📦 압축 대상 없음] 보고서 폴더 비어 있음")

def main():
    logging.info("=== VELOS 정리 루프 시작 ===")
    log_records = []
    cleanup_reports(log_records)
    cleanup_disk_usage(log_records)
    save_cleanup_log(log_records)
    backup_reports_zip()
    logging.info("=== VELOS 정리 루프 종료 ===")

if __name__ == "__main__":
    main()
