
import os
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def cleanup_old_files(directory, days_to_keep=3, extensions=None):
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    removed_files_count = 0

    for root, dirs, files in os.walk(directory):
        for file in files:
            if extensions and not file.endswith(tuple(extensions)):
                continue
            file_path = os.path.join(root, file)
            file_modified_date = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_modified_date < cutoff_date:
                os.remove(file_path)
                logging.info(f'Removed file: {file_path}')
                removed_files_count += 1

    logging.info(f'Total removed files: {removed_files_count}')

def main():
    directories_to_cleanup = {
        'C:/giwanos/data/logs': ['.log', '.jsonl', '.json'],
        'C:/giwanos/data/snapshots': ['.zip', '.bak'],  # 코드파일 (.py 등) 삭제되지 않음
        'C:/giwanos/data/reports': ['.pdf', '.md'],
        'C:/giwanos/data/reflections': ['.md', '.txt']
    }

    for directory, extensions in directories_to_cleanup.items():
        logging.info(f'Cleaning directory: {directory}')
        cleanup_old_files(directory, days_to_keep=3, extensions=extensions)

if __name__ == "__main__":
    main()
