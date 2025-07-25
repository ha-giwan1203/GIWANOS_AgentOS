
import os
import shutil
import datetime
import zipfile

SNAPSHOT_DIR = "C:/giwanos/snapshots/"
SOURCE_DIR = "C:/giwanos/"
MAX_SNAPSHOTS = 5  # 최대 보관할 스냅샷 개수

def ignore_folders(dir, files):
    ignore_list = ['snapshots', '.git', '__pycache__', 'vector_cache']
    return [f for f in files if f in ignore_list]

def create_snapshot():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_path = os.path.join(SNAPSHOT_DIR, f"snapshot_{timestamp}")

    if not os.path.exists(SNAPSHOT_DIR):
        os.makedirs(SNAPSHOT_DIR)

    # 스냅샷 생성
    shutil.copytree(SOURCE_DIR, snapshot_path, ignore=ignore_folders)

    # 생성된 스냅샷 압축(zip)
    zip_snapshot(snapshot_path)

    # 오래된 스냅샷 삭제
    cleanup_old_snapshots()

    print(f"✅ 스냅샷 및 압축 완료: {snapshot_path}.zip")

def zip_snapshot(folder_path):
    zip_path = folder_path + ".zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                zipf.write(os.path.join(root, file),
                           os.path.relpath(os.path.join(root, file),
                           os.path.join(folder_path, '..')))
    # 압축 후 원본 폴더 삭제 (권한문제 해결)
    remove_readonly(folder_path)

def remove_readonly(folder_path):
    for root, dirs, files in os.walk(folder_path, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            os.chmod(filename, 0o777)
            os.remove(filename)
        for name in dirs:
            dirname = os.path.join(root, name)
            os.chmod(dirname, 0o777)
            os.rmdir(dirname)
    os.rmdir(folder_path)

def cleanup_old_snapshots():
    snapshots = sorted(
        [f for f in os.listdir(SNAPSHOT_DIR) if f.endswith('.zip')],
        key=lambda x: os.path.getmtime(os.path.join(SNAPSHOT_DIR, x)),
        reverse=True
    )

    # 오래된 스냅샷 삭제
    for snapshot in snapshots[MAX_SNAPSHOTS:]:
        os.remove(os.path.join(SNAPSHOT_DIR, snapshot))
        print(f"🗑️ 오래된 스냅샷 삭제됨: {snapshot}")

if __name__ == "__main__":
    create_snapshot()
