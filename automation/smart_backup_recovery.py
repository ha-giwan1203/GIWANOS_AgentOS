
class SmartBackupRecovery:
    def schedule_backup(self):
        return "백업 예약 완료: 매주 일요일"

    def auto_recover(self):
        return "자동 복구 프로세스가 활성화됨"


if __name__ == "__main__":
    backup_recovery = SmartBackupRecovery()
    print(backup_recovery.schedule_backup())
    print(backup_recovery.auto_recover())
