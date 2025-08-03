import os
import time

class FileScanner:
    def __init__(self, target_folder, days_unused=90):
        self.target_folder = target_folder
        self.days_unused = days_unused

    def scan_files(self):
        file_info = []
        current_time = time.time()

        for root, dirs, files in os.walk(self.target_folder):
            for file in files:
                file_path = os.path.join(root, file)
                last_accessed = os.path.getatime(file_path)
                days_since_accessed = (current_time - last_accessed) / (24 * 3600)
                file_info.append((file_path, days_since_accessed))

        return file_info