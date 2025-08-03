import logging
import shutil
import datetime
import os

class SmartBackupRecovery:
    def __init__(self):
        self.backup_folder = 'C:/giwanos/data/backups'
        self.source_folders = ['configs', 'modules', 'scripts', 'interface']
        self.backup_interval_days = 7  # 7일에 한번만 백업
        
    def perform_backup(self):
        latest_backup = self.get_latest_backup_date()
        today = datetime.datetime.now()

        if latest_backup and (today - latest_backup).days < self.backup_interval_days:
            logging.info("최근 백업이 이미 존재하여 추가 백업을 생략합니다.")
            return True

        timestamp = today.strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_folder, f"backup_{timestamp}")
        os.makedirs(backup_path, exist_ok=True)

        for folder in self.source_folders:
            src = os.path.join('C:/giwanos', folder)
            dst = os.path.join(backup_path, folder)
            if os.path.exists(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
                logging.info(f"✅ '{folder}' 폴더 백업 완료.")
            else:
                logging.warning(f"⚠️ '{folder}' 폴더가 존재하지 않아 백업을 건너뜁니다.")

        logging.info(f"🎉 스마트 백업이 성공적으로 완료되었습니다: {backup_path}")
        self.cleanup_old_backups()
        return True

    def get_latest_backup_date(self):
        if not os.path.exists(self.backup_folder):
            return None
        backups = sorted(os.listdir(self.backup_folder), reverse=True)
        if backups:
            latest = backups[0].split('_')[1]
            return datetime.datetime.strptime(latest, "%Y%m%d")
        return None

    def cleanup_old_backups(self, retention_days=15):
        backups = os.listdir(self.backup_folder)
        today = datetime.datetime.now()
        for backup in backups:
            backup_date_str = backup.split('_')[1]
            backup_date = datetime.datetime.strptime(backup_date_str, "%Y%m%d")
            if (today - backup_date).days > retention_days:
                backup_path = os.path.join(self.backup_folder, backup)
                shutil.rmtree(backup_path)
                logging.info(f"🗑️ 오래된 백업 삭제 완료: {backup}")
