import shutil
import datetime
import os
import filecmp

SNAPSHOT_DIR = "C:/giwanos/data/snapshots"
SOURCE_DIR = "C:/giwanos/core"


def create_full_snapshot():
    snapshot_name = datetime.datetime.now().strftime("full_snapshot_%Y%m%d")
    snapshot_path = os.path.join(SNAPSHOT_DIR, snapshot_name)
    shutil.copytree(SOURCE_DIR, snapshot_path)
    print(f"Full snapshot created at: {snapshot_path}")


def create_incremental_snapshot():
    snapshots = sorted(os.listdir(SNAPSHOT_DIR))
    latest_full_snapshot = [s for s in snapshots if "full_snapshot" in s]

    if not latest_full_snapshot:
        print("No full snapshot found. Creating full snapshot instead.")
        create_full_snapshot()
        return

    latest_full_snapshot_path = os.path.join(SNAPSHOT_DIR, latest_full_snapshot[-1])
    incremental_snapshot_name = datetime.datetime.now().strftime("incremental_snapshot_%Y%m%d")
    incremental_snapshot_path = os.path.join(SNAPSHOT_DIR, incremental_snapshot_name)

    os.makedirs(incremental_snapshot_path, exist_ok=True)

    diff_files = filecmp.dircmp(SOURCE_DIR, latest_full_snapshot_path).diff_files

    for file in diff_files:
        source_file = os.path.join(SOURCE_DIR, file)
        destination_file = os.path.join(incremental_snapshot_path, file)
        shutil.copy2(source_file, destination_file)

    print(f"Incremental snapshot created at: {incremental_snapshot_path}")


def manage_snapshots():
    today = datetime.datetime.now().day

    if today == 1:
        create_full_snapshot()
    else:
        create_incremental_snapshot()


if __name__ == "__main__":
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    manage_snapshots()