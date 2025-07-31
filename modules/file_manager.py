
import shutil
import os

class FileManager:
    def __init__(self, backup_folder):
        self.backup_folder = backup_folder

    def manage_files(self, actions):
        results = {"moved": [], "kept": []}

        for action_item in actions:
            file_path = action_item["file"]
            action = action_item["action"]

            if action == "backup":
                dest_path = os.path.join(self.backup_folder, os.path.basename(file_path))
                shutil.move(file_path, dest_path)
                results["moved"].append(file_path)
            else:
                results["kept"].append(file_path)

        return results
