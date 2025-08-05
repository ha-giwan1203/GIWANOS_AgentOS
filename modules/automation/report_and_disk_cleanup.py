
"""
VELOS 시스템 통합 정리 루프 (Slack 알림 + 삭제 로그 저장 + 보고서 zip 압축 + 스케줄 실행)

- 보고서 정리: reports/, reflections/ (30일)
- 디스크 정리: logs/, snapshots/ (3일)
- 삭제 로그 저장: logs/report_cleanup_log.json
- Slack 전송 포함
- 보고서 압축: backups/weekly_report_YYYYMMDD.zip
"""

import os
import logging
import json
import zipfile
from datetime import datetime, timedelta

try:
    from tools.notifications.slack_client import send_message
except ImportError:
    def send_message(channel, text):
        print(f"[Slack 메시지 모의 전송] ({channel}): {text}")

LOG_FILE = "C:/giwanos/data/logs/report_cleanup_log.json"
SLACK_CHANNEL = "#alerts"

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def cleanup_old_files(directory, days_to_keep=30, extensions=None, log_records=None):
    cutoff = datetime.now() - timedelta(days=days_to_keep)
    count = 0

    if not os.path.exists(directory):
        logging.warning(f"대상 디렉토리 없음: {directory}")
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
                    logging.info(f"[삭제됨] {path}")
                    count += 1
                    if log_records is not None:
                        log_records.append({
                            "file": file,
                            "path": path,
                            "deleted_at": datetime.now().isoformat(),
                            "age_days": (datetime.now() - modified).days,
                            "folder": directory
                        })
            except Exception as e:
                logging.warning(f"[오류] {path} 삭제 실패: {e}")

    logging.info(f"[{directory}] → 총 {count}개 파일 삭제됨")
    return count

def cleanup_disk_usage(log_records):
    logging.info("🧹 디스크 정리 시작")
    targets = {
        "C:/giwanos/data/logs": [".log", ".jsonl", ".json"],
        "C:/giwanos/data/snapshots": [".zip", ".bak"]
    }
    total = 0
    for folder, exts in targets.items():
        total += cleanup_old_files(folder, days_to_keep=3, extensions=exts, log_records=log_records)
    return total

def cleanup_reports(log_records):
    logging.info("🧹 보고서 정리 시작")
    targets = {
        "C:/giwanos/data/reports": [".pdf", ".md", ".html", ".txt"],
        "C:/giwanos/data/reflections": [".json", ".md", ".txt"]
    }
    total = 0
    for folder, exts in targets.items():
        total += cleanup_old_files(folder, days_to_keep=30, extensions=exts, log_records=log_records)
    return total

def save_cleanup_log(log_records):
    if not log_records:
        return

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

def send_summary_to_slack(report_count, disk_count):
    total = report_count + disk_count
    if total == 0:
        msg = "[VELOS 보고] 🧼 자동 정리 루프 실행됨 – 삭제된 파일 없음"
    else:
        msg = (
            "[VELOS 보고] 🧹 정리 루프 완료\n"
            f"- 보고서 삭제: {report_count}개\n"
            f"- 로그/스냅샷 삭제: {disk_count}개\n"
            f"→ 총 {total}개 파일 삭제됨"
        )
    send_message(SLACK_CHANNEL, msg)

def backup_reports_zip():
    source_dir = "C:/giwanos/data/reports"
    backup_dir = "C:/giwanos/data/backups"
    date_str = datetime.now().strftime("%Y%m%d")
    zip_path = os.path.join(backup_dir, f"weekly_report_{date_str}.zip")

    if not os.path.exists(source_dir):
        print(f"[백업 건너뜀] 보고서 폴더가 존재하지 않음: {source_dir}")
        return

    os.makedirs(backup_dir, exist_ok=True)

    included = 0
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arcname)
                included += 1
                print(f"[백업 포함] {arcname}")

    if included == 0:
        print("[📂 보고서 폴더에 압축 대상 파일이 없습니다]")
    else:
        print(f"[✅ 보고서 압축 완료] → {zip_path}")

def main():
    logging.info("=== VELOS 정리 루프 시작 ===")
    log_records = []
    report_count = cleanup_reports(log_records)
    disk_count = cleanup_disk_usage(log_records)
    save_cleanup_log(log_records)
    send_summary_to_slack(report_count, disk_count)
    backup_reports_zip()
    logging.info("=== VELOS 정리 루프 완료 ===")

if __name__ == "__main__":
    main()
