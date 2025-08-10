import os
import shutil

class FileManager:
    def __init__(self, backup_folder):
        self.backup_folder = backup_folder

    def manage_files(self, actions):
        results = {"moved": [], "kept": []}
        for file_path in actions["move"]:
            filename = os.path.basename(file_path)
            backup_path = os.path.join(self.backup_folder, filename)
            shutil.move(file_path, backup_path)
            results["moved"].append(filename)
        results["kept"] = [os.path.basename(f) for f in actions["keep"]]
        return results

