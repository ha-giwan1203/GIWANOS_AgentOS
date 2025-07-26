
import os
import shutil
import datetime

SNAPSHOT_DIR = "C:/giwanos/snapshots/"
SOURCE_DIR = "C:/giwanos/"

def ignore_folders(dir, files):
    ignore_list = ['snapshots', '.git', '__pycache__']
    return [f for f in files if f in ignore_list]

def create_snapshot():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_path = os.path.join(SNAPSHOT_DIR, f"snapshot_{timestamp}")

    if not os.path.exists(SNAPSHOT_DIR):
        os.makedirs(SNAPSHOT_DIR)

    shutil.copytree(SOURCE_DIR, snapshot_path, ignore=ignore_folders)
    print(f"✅ Snapshot created at {snapshot_path}")

if __name__ == "__main__":
    create_snapshot()
