
import os
import shutil
import datetime
import zipfile

SNAPSHOT_DIR = "C:/giwanos/snapshots/"
SOURCE_DIRS = {
    "system": "C:/giwanos/system/",
    "data": "C:/giwanos/data/"
}
MAX_SNAPSHOTS = 5

def ignore_folders(dir, files):
    ignore_list = ['snapshots', '.git', '__pycache__', 'vector_cache']
    return [f for f in files if f in ignore_list]

def create_snapshot(folder_name, folder_path):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_path = os.path.join(SNAPSHOT_DIR, f"{folder_name}_snapshot_{timestamp}")

    if not os.path.exists(SNAPSHOT_DIR):
        os.makedirs(SNAPSHOT_DIR)

    # 개별 폴더 스냅샷 생성
    shutil.copytree(folder_path, snapshot_path, ignore=ignore_folders)
    zip_snapshot(snapshot_path)

def zip_snapshot(folder_path):
    zip_path = folder_path + ".zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                zipf.write(os.path.join(root, file),
                           os.path.relpath(os.path.join(root, file),
                           os.path.join(folder_path, '..')))
    shutil.rmtree(folder_path)

def cleanup_old_snapshots():
    snapshots = sorted(
        [f for f in os.listdir(SNAPSHOT_DIR) if f.endswith('.zip')],
        key=lambda x: os.path.getmtime(os.path.join(SNAPSHOT_DIR, x)),
        reverse=True
    )
    for snapshot in snapshots[MAX_SNAPSHOTS:]:
        os.remove(os.path.join(SNAPSHOT_DIR, snapshot))
        print(f"🗑️ 오래된 스냅샷 삭제됨: {snapshot}")

def main():
    for name, path in SOURCE_DIRS.items():
        create_snapshot(name, path)
    cleanup_old_snapshots()
    print(f"✅ 멀티 폴더 스냅샷 완료")

if __name__ == "__main__":
    main()
