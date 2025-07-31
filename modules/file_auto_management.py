
from file_scanner import FileScanner
from judge_agent import JudgeAgent
from file_manager import FileManager
import os

def file_auto_management(target_folder, backup_folder, days_unused=90):
    os.makedirs(backup_folder, exist_ok=True)

    scanner = FileScanner(target_folder, days_unused)
    file_info = scanner.scan_files()

    agent = JudgeAgent()
    actions = agent.evaluate_files(file_info, days_unused)

    manager = FileManager(backup_folder)
    results = manager.manage_files(actions)

    return results

if __name__ == "__main__":
    target = "C:/giwanos/data/logs"  # 명확한 하위 폴더 지정
    backup = "C:/giwanos_backup"
    print(file_auto_management(target, backup))
